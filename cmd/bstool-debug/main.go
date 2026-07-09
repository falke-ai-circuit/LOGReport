package main

import (
	"encoding/binary"
	"encoding/hex"
	"fmt"
	"net"
	"os"
	"time"
)

// Block header: 20 bytes, big-endian
// Command(2) + Sequence(2) + Source(4) + Dest(4) + Param(4) + DataLen(4)
type BlockHeader struct {
	Command  uint16
	Sequence uint16
	Source   uint32
	Dest     uint32
	Param    uint32
	DataLen  uint32
	Size     uint32 // not in header, from response
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
	// Read data
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

	// Handshake: 3x cmd=0x0C
	fmt.Println("\n--- Handshake ---")
	for i := 0; i < 3; i++ {
		hsBlock := &Block{
			Header: BlockHeader{
				Command:  CmdHandshake,
				Sequence: 0x0136,
				Source:   0x00EFD61C,
			},
		}
		if err := sendBlock(conn, hsBlock); err != nil {
			fmt.Printf("HS send[%d]: %v\n", i, err)
			os.Exit(1)
		}
		resp, err := recvBlock(conn)
		if err != nil {
			fmt.Printf("HS recv[%d]: %v\n", i, err)
			os.Exit(1)
		}
		fmt.Printf("HS[%d]: cmd=0x%04x seq=0x%04x src=0x%08x dst=0x%08x param=0x%08x dlen=%d\n",
			i, resp.Header.Command, resp.Header.Sequence, resp.Header.Source, resp.Header.Dest, resp.Header.Param, resp.Header.DataLen)
		if len(resp.Data) > 0 {
			fmt.Printf("  data: %s\n", hex.Dump(resp.Data[:min(len(resp.Data), 64)]))
		}
	}

	// Test 1: READ_DIR with :s:AB01:*.sys
	fmt.Println("\n--- READ_DIR :s:AB01:*.sys ---")
	dirPath := fmt.Sprintf(":s:%s:*.sys\x00", commLine)
	readDirBlock := &Block{
		Header: BlockHeader{
			Command:  CmdReadDir,
			Source:   0x00EFD61C,
			DataLen:  uint32(len(dirPath)),
		},
		Data: []byte(dirPath),
	}
	if err := sendBlock(conn, readDirBlock); err != nil {
		fmt.Printf("READ_DIR send: %v\n", err)
		os.Exit(1)
	}
	resp, err := recvBlock(conn)
	if err != nil {
		fmt.Printf("READ_DIR recv: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("READ_DIR resp: cmd=0x%04x src=0x%08x dst=0x%08x param=0x%08x dlen=%d\n",
		resp.Header.Command, resp.Header.Source, resp.Header.Dest, resp.Header.Param, resp.Header.DataLen)
	if len(resp.Data) > 0 {
		fmt.Printf("  data: %s\n", hex.Dump(resp.Data[:min(len(resp.Data), 128)]))
	}
	cursor := resp.Header.Param

	// Test 2: GET_DIR_ENTRY iterations
	fmt.Println("\n--- GET_DIR_ENTRY iterations ---")
	entryCount := 0
	for cursor != 0 && entryCount < 50 {
		entryBlock := &Block{
			Header: BlockHeader{
				Command: CmdGetDirEntry,
				Source:  0x00EFD61C,
				Param:   cursor,
			},
		}
		if err := sendBlock(conn, entryBlock); err != nil {
			fmt.Printf("GET_DIR_ENTRY send: %v\n", err)
			break
		}
		entryResp, err := recvBlock(conn)
		if err != nil {
			fmt.Printf("GET_DIR_ENTRY recv: %v\n", err)
			break
		}
		fmt.Printf("Entry[%d]: cmd=0x%04x param=0x%08x dlen=%d src=0x%08x size=?\n",
			entryCount, entryResp.Header.Command, entryResp.Header.Param, entryResp.Header.DataLen, entryResp.Header.Source)
		if len(entryResp.Data) > 0 {
			// Print raw data and try to extract filename
			fmt.Printf("  raw: %s\n", hex.Dump(entryResp.Data[:min(len(entryResp.Data), 64)]))
			// Also print as string (stop at first null)
			str := string(entryResp.Data)
			for i, c := range str {
				if c == 0 {
					str = str[:i]
					break
				}
			}
			fmt.Printf("  name: %q\n", str)
		}
		cursor = entryResp.Header.Param
		entryCount++
	}
	fmt.Printf("Total entries: %d\n", entryCount)

	// Test 3: Try FILE_OPEN with a known filename
	fmt.Println("\n--- FILE_OPEN :s:AB01:161.sys ---")
	openPath := fmt.Sprintf(":s:%s:161.sys\x00rb\x00", commLine)
	openBlock := &Block{
		Header: BlockHeader{
			Command: CmdFileOpen,
			Source:  0x00EFD61C,
			DataLen: uint32(len(openPath)),
		},
		Data: []byte(openPath),
	}
	if err := sendBlock(conn, openBlock); err != nil {
		fmt.Printf("FILE_OPEN send: %v\n", err)
	} else {
		openResp, err := recvBlock(conn)
		if err != nil {
			fmt.Printf("FILE_OPEN recv: %v\n", err)
		} else {
			fmt.Printf("FILE_OPEN resp: cmd=0x%04x src=0x%08x param=0x%08x dlen=%d\n",
				openResp.Header.Command, openResp.Header.Source, openResp.Header.Param, openResp.Header.DataLen)
			if len(openResp.Data) > 0 {
				fmt.Printf("  data: %s\n", hex.Dump(openResp.Data[:min(len(openResp.Data), 64)]))
			}
			fileHandle := openResp.Header.Source
			if fileHandle != 0 && fileHandle != 0xFFFFFFFF {
				// Read first chunk
				fmt.Println("\n--- FILE_READ ---")
				readBlock := &Block{
					Header: BlockHeader{
						Command: CmdFileRead,
						Source:  fileHandle,
						Param:   448,
					},
				}
				if err := sendBlock(conn, readBlock); err != nil {
					fmt.Printf("FILE_READ send: %v\n", err)
				} else {
					readResp, err := recvBlock(conn)
					if err != nil {
						fmt.Printf("FILE_READ recv: %v\n", err)
					} else {
						fmt.Printf("FILE_READ resp: cmd=0x%04x src=0x%08x param=0x%08x dlen=%d datalen=%d\n",
							readResp.Header.Command, readResp.Header.Source, readResp.Header.Param, readResp.Header.DataLen, len(readResp.Data))
						if len(readResp.Data) > 0 {
							fmt.Printf("  data: %s\n", hex.Dump(readResp.Data[:min(len(readResp.Data), 128)]))
						}
					}
				}
				// Close file
				closeBlock := &Block{
					Header: BlockHeader{
						Command: CmdFileClose,
						Source:  fileHandle,
					},
				}
				sendBlock(conn, closeBlock)
				recvBlock(conn)
			}
		}
	}

	// Test 4: Try READ_DIR without glob — just :s:AB01
	fmt.Println("\n--- READ_DIR :s:AB01 (no glob) ---")
	dirPath2 := fmt.Sprintf(":s:%s\x00", commLine)
	readDirBlock2 := &Block{
		Header: BlockHeader{
			Command:  CmdReadDir,
			Source:   0x00EFD61C,
			DataLen:  uint32(len(dirPath2)),
		},
		Data: []byte(dirPath2),
	}
	if err := sendBlock(conn, readDirBlock2); err != nil {
		fmt.Printf("READ_DIR send: %v\n", err)
	} else {
		resp2, err := recvBlock(conn)
		if err != nil {
			fmt.Printf("READ_DIR recv: %v\n", err)
		} else {
			fmt.Printf("READ_DIR resp: cmd=0x%04x param=0x%08x dlen=%d\n",
				resp2.Header.Command, resp2.Header.Param, resp2.Header.DataLen)
			if len(resp2.Data) > 0 {
				fmt.Printf("  data: %s\n", hex.Dump(resp2.Data[:min(len(resp2.Data), 64)]))
			}
			cursor2 := resp2.Header.Param
			count2 := 0
			for cursor2 != 0 && count2 < 10 {
				entryBlock2 := &Block{
					Header: BlockHeader{
						Command: CmdGetDirEntry,
						Source:  0x00EFD61C,
						Param:   cursor2,
					},
				}
				sendBlock(conn, entryBlock2)
				entryResp2, err := recvBlock(conn)
				if err != nil {
					break
				}
				if len(entryResp2.Data) > 0 {
					str := string(entryResp2.Data)
					for i, c := range str {
						if c == 0 {
							str = str[:i]
							break
						}
					}
					fmt.Printf("  Entry[%d]: %q param=0x%08x\n", count2, str, entryResp2.Header.Param)
				}
				cursor2 = entryResp2.Header.Param
				count2++
			}
			fmt.Printf("  Total: %d\n", count2)
		}
	}

	fmt.Println("\nDone!")
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}