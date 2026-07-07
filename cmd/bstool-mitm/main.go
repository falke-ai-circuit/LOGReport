package main

import (
	"encoding/binary"
	"encoding/hex"
	"fmt"
	"io"
	"net"
	"os"
	"sync"
	"time"
)

// MITM proxy: listen on port 1517, forward to 127.0.0.1:1516
// Capture all traffic in both directions

func main() {
	listenAddr := "0.0.0.0:1517"
	targetAddr := "127.0.0.1:1516"

	ln, err := net.Listen("tcp", listenAddr)
	if err != nil {
		fmt.Printf("Listen error: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("MITM proxy listening on %s, forwarding to %s\n", listenAddr, targetAddr)
	fmt.Println("Run: set COMMUNICATION_LINE=AB01 && BsTool.exe -ls :s:AB01:*.sys -noconn localhost:1517")
	fmt.Println("Waiting for connection...")

	for {
		conn, err := ln.Accept()
		if err != nil {
			continue
		}
		go handleConn(conn, targetAddr)
	}
}

func handleConn(client net.Conn, target string) {
	server, err := net.DialTimeout("tcp", target, 10*time.Second)
	if err != nil {
		fmt.Printf("Dial target error: %v\n", err)
		client.Close()
		return
	}
	defer client.Close()
	defer server.Close()

	fmt.Printf("\n=== New connection from %s ===\n", client.RemoteAddr())

	var wg sync.WaitGroup
	wg.Add(2)

	// Client -> Server
	go func() {
		defer wg.Done()
		buf := make([]byte, 4096)
		for {
			n, err := client.Read(buf)
			if n > 0 {
				fmt.Printf("\n>>> CLIENT -> SERVER (%d bytes):\n", n)
				fmt.Printf("%s\n", hex.Dump(buf[:n]))
				// Parse block header if enough bytes
				if n >= 20 {
					cmd := binary.BigEndian.Uint16(buf[0:2])
					seq := binary.BigEndian.Uint16(buf[2:4])
					src := binary.BigEndian.Uint32(buf[4:8])
					dst := binary.BigEndian.Uint32(buf[8:12])
					param := binary.BigEndian.Uint32(buf[12:16])
					dlen := binary.BigEndian.Uint32(buf[16:20])
					fmt.Printf("    cmd=0x%04x seq=0x%04x src=0x%08x dst=0x%08x param=0x%08x dlen=%d\n", cmd, seq, src, dst, param, dlen)
					if dlen > 0 && n > 20 {
						fmt.Printf("    data: %q\n", string(buf[20:min(int(20+dlen), n)]))
					}
				}
				server.Write(buf[:n])
			}
			if err != nil || err == io.EOF {
				break
			}
		}
	}()

	// Server -> Client
	go func() {
		defer wg.Done()
		buf := make([]byte, 4096)
		for {
			n, err := server.Read(buf)
			if n > 0 {
				fmt.Printf("\n<<< SERVER -> CLIENT (%d bytes):\n", n)
				fmt.Printf("%s\n", hex.Dump(buf[:n]))
				if n >= 20 {
					cmd := binary.BigEndian.Uint16(buf[0:2])
					seq := binary.BigEndian.Uint16(buf[2:4])
					src := binary.BigEndian.Uint32(buf[4:8])
					dst := binary.BigEndian.Uint32(buf[8:12])
					param := binary.BigEndian.Uint32(buf[12:16])
					dlen := binary.BigEndian.Uint32(buf[16:20])
					fmt.Printf("    cmd=0x%04x seq=0x%04x src=0x%08x dst=0x%08x param=0x%08x dlen=%d\n", cmd, seq, src, dst, param, dlen)
					if dlen > 0 && n > 20 {
						fmt.Printf("    data: %q\n", string(buf[20:min(int(20+dlen), n)]))
					}
				}
				client.Write(buf[:n])
			}
			if err != nil || err == io.EOF {
				break
			}
		}
	}()

	wg.Wait()
	fmt.Printf("=== Connection closed ===\n")
}

func min(a, b int) int {
	if a < b { return a }
	return b
}