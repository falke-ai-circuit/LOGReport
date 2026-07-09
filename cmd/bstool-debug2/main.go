package main

import (
	"encoding/binary"
	"encoding/hex"
	"fmt"
	"net"
	"os"
	"time"
)

type BlockHeader struct {
	Command  uint16
	Sequence uint16
	Source   uint32
	Dest     uint32
	Param    uint32
	DataLen  uint32
}

type Block struct {
	Header BlockHeader
	Data   []byte
}

const (
	CmdHandshake   = 0x000C
	CmdReadDir     = 0x0014
	CmdGetDirEntry = 0x0016
	CmdFileOpen    = 0x0000
	CmdFileRead    = 0x0002
	CmdFileClose   = 0x0001
	CmdFileInit    = 0x0005
	CmdSendCmd     = 0x000A
)

func sendBlock(conn net.Conn, blk *Block) error {
	buf := make([]byte, 20)
	binary.BigEndian.PutUint16(buf[0:2], blk.Header.Command)
	binary.BigEndian.PutUint16(buf[2:4], blk.Header.Sequence)
	binary.BigEndian.PutUint32(buf[4:8], blk.Header.Source)
	binary.BigEndian.PutUint32(buf[8:12], blk.Header.Dest)
	binary.BigEndian.PutUint32(buf[12:16], blk.Header.Param)
	binary.BigEndian.PutUint32(buf[16:20], blk.Header.DataLen)
	if len(blk.Data) > 0 {
		buf = append(buf, blk.Data...)
	}
	_, err := conn.Write(buf)
	return err
}

func recvBlock(conn net.Conn) (*Block, error) {
	header := make([]byte, 20)
	if _, err := readFull(conn, header); err != nil {
		return nil, fmt.Errorf("recv header: %w", err)
	}
	blk := &Block{
		Header: BlockHeader{
			Command:  binary.BigEndian.Uint16(header[0:2]),
			Sequence: binary.BigEndian.Uint16(header[2:4]),
			Source:   binary.BigEndian.Uint32(header[4:8]),
			Dest:     binary.BigEndian.Uint32(header[8:12]),
			Param:    binary.BigEndian.Uint32(header[12:16]),
			DataLen:  binary.BigEndian.Uint32(header[16:20]),
		},
	}
	if blk.Header.DataLen > 0 && blk.Header.DataLen < 1024*1024 {
		data := make([]byte, blk.Header.DataLen)
		if _, err := readFull(conn, data); err != nil {
			return blk, fmt.Errorf("recv data: %w", err)
		}
		blk.Data = data
	}
	return blk, nil
}

func readFull(conn net.Conn, buf []byte) (int, error) {
	total := 0
	for total < len(buf) {
		n, err := conn.Read(buf[total:])
		if err != nil {
			return total, err
		}
		total += n
	}
	return total, nil
}

func min(a, b int) int {
	if a < b { return a }
	return b
}

func sendAndRecv(conn net.Conn, name string, blk *Block) (*Block, error) {
	fmt.Printf("\n--- %s ---\n", name)
	fmt.Printf("SEND: cmd=0x%04x seq=0x%04x src=0x%08x dst=0x%08x param=0x%08x dlen=%d\n",
		blk.Header.Command, blk.Header.Sequence, blk.Header.Source, blk.Header.Dest, blk.Header.Param, blk.Header.DataLen)
	if len(blk.Data) > 0 {
		fmt.Printf("  data: %s\n", hex.Dump(blk.Data[:min(len(blk.Data), 64)]))
	}
	if err := sendBlock(conn, blk); err != nil {
		return nil, fmt.Errorf("send: %w", err)
	}
	resp, err := recvBlock(conn)
	if err != nil {
		return nil, fmt.Errorf("recv: %w", err)
	}
	fmt.Printf("RECV: cmd=0x%04x seq=0x%04x src=0x%08x dst=0x%08x param=0x%08x dlen=%d\n",
		resp.Header.Command, resp.Header.Sequence, resp.Header.Source, resp.Header.Dest, resp.Header.Param, resp.Header.DataLen)
	if len(resp.Data) > 0 {
		fmt.Printf("  data: %s\n", hex.Dump(resp.Data[:min(len(resp.Data), 128)]))
	}
	return resp, nil
}

func main() {
	host := "127.0.0.1"
	port := 1516
	commLine := "AB01"

	fmt.Printf("Connecting to %s:%d (commLine=%s)\n", host, port, commLine)
	conn, err := net.DialTimeout("tcp", fmt.Sprintf("%s:%d", host, port), 10*time.Second)
	if err != nil {
		fmt.Printf("Connect error: %v\n", err)
		os.Exit(1)
	}
	defer conn.Close()
	fmt.Println("Connected!")

	// Handshake
	for i := 0; i < 3; i++ {
		hsBlock := &Block{
			Header: BlockHeader{
				Command:  CmdHandshake,
				Sequence: 0x0136,
				Source:   0x00EFD61C,
			},
		}
		sendBlock(conn, hsBlock)
		resp, _ := recvBlock(conn)
		fmt.Printf("HS[%d]: param=0x%08x\n", i, resp.Header.Param)
	}

	// Test A: FILE_INIT (0x05) with commLine
	initData := fmt.Sprintf(":s:%s\x00", commLine)
	sendAndRecv(conn, "FILE_INIT", &Block{
		Header: BlockHeader{
			Command: CmdFileInit,
			Source:  0x00EFD61C,
			DataLen: uint32(len(initData)),
		},
		Data: []byte(initData),
	})

	// Test B: Try READ_DIR after FILE_INIT
	dirPath := fmt.Sprintf(":s:%s:*.sys\x00", commLine)
	resp, err := sendAndRecv(conn, "READ_DIR after INIT", &Block{
		Header: BlockHeader{
			Command: CmdReadDir,
			Source:  0x00EFD61C,
			DataLen: uint32(len(dirPath)),
		},
		Data: []byte(dirPath),
	})
	if err == nil && resp.Header.Param != 0 {
		fmt.Printf("\nREAD_DIR returned cursor=0x%08x — SUCCESS!\n", resp.Header.Param)
		// Iterate entries
		cursor := resp.Header.Param
		for i := 0; cursor != 0 && i < 50; i++ {
			entryResp, err := sendAndRecv(conn, fmt.Sprintf("GET_DIR_ENTRY[%d]", i), &Block{
				Header: BlockHeader{
					Command: CmdGetDirEntry,
					Source:  0x00EFD61C,
					Param:   cursor,
				},
			})
			if err != nil {
				break
			}
			cursor = entryResp.Header.Param
		}
	}

	// Test C: Try FILE_OPEN and FILE_READ on 161.sys with different approaches
	// Approach 1: Standard FILE_OPEN
	openPath := fmt.Sprintf(":s:%s:161.sys\x00rb\x00", commLine)
	openResp, err := sendAndRecv(conn, "FILE_OPEN 161.sys", &Block{
		Header: BlockHeader{
			Command: CmdFileOpen,
			Source:  0x00EFD61C,
			DataLen: uint32(len(openPath)),
		},
		Data: []byte(openPath),
	})
	if err == nil && openResp.Header.Source != 0 && openResp.Header.Source != 0xFFFFFFFF {
		handle := openResp.Header.Source
		// Try FILE_READ with different param values
		for _, param := range []uint32{448, 0, 2048, 1024, 512, 256, 128, 64, 32, 16, 8, 1} {
			readResp, err := sendAndRecv(conn, fmt.Sprintf("FILE_READ param=%d", param), &Block{
				Header: BlockHeader{
					Command: CmdFileRead,
					Source:  handle,
					Param:   param,
				},
			})
			if err != nil {
				fmt.Printf("  FILE_READ error: %v\n", err)
				break
			}
			if len(readResp.Data) > 0 {
				fmt.Printf("  GOT DATA: %d bytes!\n", len(readResp.Data))
				break
			}
		}
		// Close file
		sendBlock(conn, &Block{
			Header: BlockHeader{
				Command: CmdFileClose,
				Source:  handle,
			},
		})
		recvBlock(conn)
	}

	// Test D: Try with Dest field set (maybe Dest needs to be set for file ops)
	// Reconnect for clean state
	conn.Close()
	conn, _ = net.DialTimeout("tcp", fmt.Sprintf("%s:%d", host, port), 10*time.Second)
	defer conn.Close()
	for i := 0; i < 3; i++ {
		sendBlock(conn, &Block{Header: BlockHeader{Command: CmdHandshake, Sequence: 0x0136, Source: 0x00EFD61C}})
		recvBlock(conn)
	}

	// Try READ_DIR with Dest=0x02CC (the value BU returned in handshake)
	dirPath2 := fmt.Sprintf(":s:%s:*.sys\x00", commLine)
	resp2, err := sendAndRecv(conn, "READ_DIR with Dest=0x02CC", &Block{
		Header: BlockHeader{
			Command: CmdReadDir,
			Source:  0x00EFD61C,
			Dest:    0x02CC,
			DataLen: uint32(len(dirPath2)),
		},
		Data: []byte(dirPath2),
	})
	if err == nil && resp2.Header.Param != 0 {
		fmt.Printf("\nREAD_DIR with Dest returned cursor=0x%08x — SUCCESS!\n", resp2.Header.Param)
	}

	// Test E: Try command 0x0A (zzSendCmd) with READ_DIR as a sub-command
	sendAndRecv(conn, "SEND_CMD 0x0A", &Block{
		Header: BlockHeader{
			Command: CmdSendCmd,
			Source:  0x00EFD61C,
			DataLen: uint32(len(dirPath2)),
		},
		Data: []byte(dirPath2),
	})

	fmt.Println("\nDone!")
}