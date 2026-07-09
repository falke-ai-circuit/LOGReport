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

func connectAndHandshake(host string, port int) net.Conn {
	conn, err := net.DialTimeout("tcp", fmt.Sprintf("%s:%d", host, port), 10*time.Second)
	if err != nil {
		fmt.Printf("Connect error: %v\n", err)
		os.Exit(1)
	}
	for i := 0; i < 3; i++ {
		sendBlock(conn, &Block{Header: BlockHeader{Command: CmdHandshake, Sequence: 0x0136, Source: 0x00EFD61C}})
		resp, _ := recvBlock(conn)
		fmt.Printf("HS[%d]: dst=0x%08x\n", i, resp.Header.Dest)
	}
	return conn
}

func main() {
	host := "127.0.0.1"
	port := 1516
	commLine := "AB01"

	// Test 1: Fresh connection for READ_DIR
	fmt.Println("=== Test 1: Fresh connection + READ_DIR ===")
	conn := connectAndHandshake(host, port)
	dirPath := fmt.Sprintf(":s:%s:*.sys\x00", commLine)
	fmt.Printf("SEND READ_DIR: %q\n", dirPath)
	sendBlock(conn, &Block{
		Header: BlockHeader{Command: CmdReadDir, Source: 0x00EFD61C, DataLen: uint32(len(dirPath))},
		Data:   []byte(dirPath),
	})
	resp, err := recvBlock(conn)
	if err != nil {
		fmt.Printf("READ_DIR error: %v\n", err)
	} else {
		fmt.Printf("READ_DIR resp: cmd=0x%04x param=0x%08x dlen=%d\n", resp.Header.Command, resp.Header.Param, resp.Header.DataLen)
		if len(resp.Data) > 0 {
			fmt.Printf("  data: %s\n", hex.Dump(resp.Data[:min(len(resp.Data), 128)]))
		}
		if resp.Header.Param != 0 {
			fmt.Printf("  CURSOR = 0x%08x — SUCCESS!\n", resp.Header.Param)
			cursor := resp.Header.Param
			for i := 0; cursor != 0 && i < 50; i++ {
				sendBlock(conn, &Block{Header: BlockHeader{Command: CmdGetDirEntry, Source: 0x00EFD61C, Param: cursor}})
				entryResp, err := recvBlock(conn)
				if err != nil {
					fmt.Printf("  GET_DIR_ENTRY[%d] error: %v\n", i, err)
					break
				}
				if len(entryResp.Data) > 0 {
					str := string(entryResp.Data)
					for j, c := range str {
						if c == 0 { str = str[:j]; break }
					}
					fmt.Printf("  Entry[%d]: %q (param=0x%08x)\n", i, str, entryResp.Header.Param)
				}
				cursor = entryResp.Header.Param
			}
		}
	}
	conn.Close()

	// Test 2: Fresh connection + FILE_OPEN + FILE_READ
	fmt.Println("\n=== Test 2: Fresh connection + FILE_OPEN + FILE_READ ===")
	conn = connectAndHandshake(host, port)
	openPath := fmt.Sprintf(":s:%s:161.sys\x00rb\x00", commLine)
	fmt.Printf("SEND FILE_OPEN: %q\n", openPath)
	sendBlock(conn, &Block{
		Header: BlockHeader{Command: CmdFileOpen, Source: 0x00EFD61C, DataLen: uint32(len(openPath))},
		Data:   []byte(openPath),
	})
	openResp, err := recvBlock(conn)
	if err != nil {
		fmt.Printf("FILE_OPEN error: %v\n", err)
	} else {
		fmt.Printf("FILE_OPEN resp: src=0x%08x (handle)\n", openResp.Header.Source)
		handle := openResp.Header.Source
		if handle != 0 && handle != 0xFFFFFFFF {
			// Read first chunk
			sendBlock(conn, &Block{Header: BlockHeader{Command: CmdFileRead, Source: handle, Param: 448}})
			readResp, err := recvBlock(conn)
			if err != nil {
				fmt.Printf("FILE_READ error: %v\n", err)
			} else {
				fmt.Printf("FILE_READ resp: dlen=%d datalen=%d\n", readResp.Header.DataLen, len(readResp.Data))
				if len(readResp.Data) > 0 {
					fmt.Printf("  GOT %d bytes of file data!\n", len(readResp.Data))
					fmt.Printf("  first 128 bytes: %s\n", hex.Dump(readResp.Data[:min(len(readResp.Data), 128)]))
				} else {
					fmt.Println("  No data returned (0 bytes)")
				}
			}
			// Close
			sendBlock(conn, &Block{Header: BlockHeader{Command: CmdFileClose, Source: handle}})
			recvBlock(conn)
		}
	}
	conn.Close()

	fmt.Println("\nDone!")
}