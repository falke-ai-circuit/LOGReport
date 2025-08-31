# Validation Test Plan

## 1. Token Detection Test Cases
- [x] Valid FBC token extraction
- [x] Valid RPC token extraction
- [x] Invalid token handling
- [x] Unknown node token handling
- [ ] Token extraction performance test

## 2. Node Display Verification
- [x] Context menu shows correct tokens
- [x] Tokens displayed in sorted order
- [x] Mixed-case filename handling
- [ ] Node tree refresh after token updates

## 3. Session Persistence Tests
- [ ] Session state after application restart
- [ ] Session recovery after crash
- [ ] Long-running session stability
- [ ] Multiple session management

## 4. Error Handling Validation
- [x] Invalid token format handling
- [ ] Network error during token detection
- [ ] File permission errors
- [ ] Corrupted log file handling
- [ ] Error reporting UI validation

## 5. Mixed-case Filename Handling
- [x] Token extraction from mixed-case filenames
- [ ] Session persistence with mixed-case paths
- [ ] Error handling with mixed-case paths
- [ ] Case-insensitive token matching