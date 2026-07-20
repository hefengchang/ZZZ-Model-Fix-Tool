try:
    from colorama import Fore, Back, init
except ImportError:
    import subprocess, sys, os
    print("未检测到 colorama 库，正在自动安装...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "colorama"])
    print("colorama 安装完成，正在重新运行脚本...")
    os.execl(sys.executable, sys.executable, *sys.argv)

import os
import threading
from datetime import datetime
import sys

class HashConflictChecker:
    def __init__(self):
        """初始化Hash冲突检查器"""
        self.hash_table = {}  # 存储每个MOD的hash集合，格式: {mod_name: {hash_value: file_path}}
        self.conflict_list = []  # 存储冲突信息
        self.ignore_list = set()  # 忽略的hash值
        # 添加需要忽略的特定hash值
        self.ignore_list.add("ebac056e")
        self.ignore_list.add("798adba3")
        self.ignore_list.add("d9a12c0a")
        self.ignore_ini_list = set()  # 忽略的ini文件
        self.lock = threading.RLock()
        self.last_check_time = None
    
    def load_ignore_list(self, file_path):
        """加载忽略的hash列表"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as file:
                    for line in file:
                        line = line.strip()
                        if line:  # 跳过空行
                            self.ignore_list.add(line)
                print(f"{Fore.GREEN}已加载忽略hash列表: {file_path}{Fore.RESET}")
        except Exception as e:
            print(f"{Fore.RED}读取忽略hash列表失败: {e}{Fore.RESET}")
    
    def load_ignore_ini_list(self, file_path):
        """加载忽略的ini文件列表"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as file:
                    for line in file:
                        line = line.strip()
                        if line:  # 跳过空行
                            self.ignore_ini_list.add(line)
                print(f"{Fore.GREEN}已加载忽略ini文件列表: {file_path}{Fore.RESET}")
        except Exception as e:
            print(f"{Fore.RED}读取忽略ini文件列表失败: {e}{Fore.RESET}")
    
    def get_hash_list(self, ini_file):
        """从INI文件中提取hash值，返回字典格式: {hash_value: file_path}"""
        hash_dict = {}
        
        try:
            with open(ini_file, "r", encoding="utf-8") as fobj:
                contents = fobj.readlines()
            
            for line in contents:
                # 去除行首空白字符
                line = line.lstrip()
                
                # 跳过空行和纯注释行
                if not line or line.startswith(';'):
                    continue
                
                # 去除行尾注释
                if ';' in line:
                    line = line.split(';')[0].rstrip()
                
                if '=' in line:
                    data = line.split('=')
                    if len(data) != 2:
                        continue
                    
                    key, value = data
                    key = key.strip()
                    value = value.strip()
                    
                    if key.lower() == 'hash' and value not in self.ignore_list:
                        hash_dict[value] = ini_file
        except Exception as e:
            print(f"{Fore.RED}读取文件 {ini_file} 失败: {e}{Fore.RESET}")
        
        return hash_dict
    
    def scan_directory(self, base_dir):
        """扫描目录及其子目录，提取所有INI文件的hash值"""
        with self.lock:
            self.hash_table = {}  # 重置hash表
            total_files_scanned = 0
            total_hash_extracted = 0
            
            # 遍历目录
            for root, dirs, files in os.walk(base_dir):
                # 跳过以disabled开头的文件夹
                dirs[:] = [d for d in dirs if not d.lower().startswith("disabled")]
                
                for file in files:
                    if file.endswith(".ini") and not file.lower().startswith("disabled"):
                        if file in self.ignore_ini_list:
                            continue
                        
                        ini_path = os.path.join(root, file)
                        # 使用相对路径作为MOD标识，去除基础目录部分
                        mod_identifier = os.path.relpath(ini_path, base_dir)
                        # 提取MOD目录名称（使用第一级子目录作为MOD名称）
                        mod_name = mod_identifier.split(os.path.sep)[0]
                        
                        # 如果MOD不存在，创建新的hash字典
                        if mod_name not in self.hash_table:
                            self.hash_table[mod_name] = {}
                        
                        # 添加当前文件的hash值和文件路径
                        hash_dict = self.get_hash_list(ini_path)
                        self.hash_table[mod_name].update(hash_dict)
                        
                        total_files_scanned += 1
                        total_hash_extracted += len(hash_dict)
            
            print(f"\n{Fore.MAGENTA}共扫描 {total_files_scanned} 个文件，提取 {total_hash_extracted} 个hash值{Fore.RESET}")
            print(f"{Fore.MAGENTA}共扫描到 {len(self.hash_table)} 个MOD目录{Fore.RESET}")
            self.check_conflicts()
    
    def check_conflicts(self):
        """检查所有MOD之间的hash冲突"""
        with self.lock:
            self.conflict_list = []
            self.last_check_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            mod_list = list(self.hash_table.keys())
            total_comparisons = 0
            
            for i in range(len(mod_list)):
                mod1 = mod_list[i]
                for j in range(i + 1, len(mod_list)):
                    mod2 = mod_list[j]
                    # 获取两个MOD的hash值集合
                    hash_set1 = set(self.hash_table[mod1].keys())
                    hash_set2 = set(self.hash_table[mod2].keys())
                    # 计算交集
                    intersection = hash_set1 & hash_set2
                    if intersection:
                        # 收集冲突hash值及其文件路径
                        conflict_details = []
                        for hash_val in intersection:
                            file1 = self.hash_table[mod1][hash_val]
                            file2 = self.hash_table[mod2][hash_val]
                            conflict_details.append({
                                "hash": hash_val,
                                "file1": file1,
                                "file2": file2
                            })
                        self.conflict_list.append({
                            "mod1": mod1,
                            "mod2": mod2,
                            "intersection": intersection,
                            "details": conflict_details
                        })
                    total_comparisons += 1
            
            print(f"{Fore.MAGENTA}共进行 {total_comparisons} 次MOD对比{Fore.RESET}")
            
            if self.conflict_list:
                print(f"{Fore.RED}检测到 {len(self.conflict_list)} 个hash冲突{Fore.RESET}")
                self.show_conflicts()
            else:
                print(f"{Fore.GREEN}未检测到hash冲突{Fore.RESET}")
    
    def show_conflicts(self):
        """显示冲突信息"""
        print(f"\n[{self.last_check_time}] Hash冲突检测结果:")
        print("=" * 80)
        
        for i, conflict in enumerate(self.conflict_list, 1):
            print(f"\n冲突 #{i}:")
            print(f"MOD 1: {Fore.YELLOW}{conflict['mod1']}{Fore.RESET}")
            print(f"MOD 2: {Fore.YELLOW}{conflict['mod2']}{Fore.RESET}")
            print(f"冲突的hash值: {Fore.GREEN}{', '.join(conflict['intersection'])}{Fore.RESET}")
        
        print("=" * 80)
    
    def search_conflicts(self, search_terms):
        """根据搜索条件筛选冲突"""
        if not search_terms:
            return self.conflict_list
        
        results = []
        terms = search_terms.split(" ")
        
        for conflict in self.conflict_list:
            # 构建搜索内容
            content = [
                conflict["mod1"],
                conflict["mod2"],
                *conflict["intersection"]
            ]
            # 添加文件路径到搜索内容
            for detail in conflict['details']:
                content.append(detail['file1'])
                content.append(detail['file2'])
            
            # 检查是否匹配所有搜索条件
            match = True
            for term in terms:
                if term.startswith("!"):
                    # 排除条件
                    term = term[1:]
                    if any(term in str(item) for item in content):
                        match = False
                        break
                else:
                    # 包含条件
                    if not any(term in str(item) for item in content):
                        match = False
                        break
            
            if match:
                results.append(conflict)
        
        return results

def main():
    """主函数"""
    # 初始化colorama
    init()
    
    # 获取当前程序所在目录（兼容py和exe两种情况）
    if getattr(sys, 'frozen', False):
        current_dir = os.path.dirname(sys.executable)
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
    
    os.chdir(current_dir)
    print(f"{Fore.CYAN}当前扫描目录: {current_dir}{Fore.RESET}")
    
    # 创建检查器实例
    checker = HashConflictChecker()
    
    # 加载忽略列表
    checker.load_ignore_list(os.path.join(current_dir, '忽略hash表.txt'))
    checker.load_ignore_ini_list(os.path.join(current_dir, '忽略ini文件表.txt'))
    
    # 扫描目录
    checker.scan_directory(current_dir)
    
    # 搜索冲突
    print("\n输入搜索关键词显示具体信息（多个关键词用空格分隔，排除关键词用!开头），输入 'exit' 退出搜索:")
    
    while True:
        search_input = input("> ")
        
        if search_input.lower() == 'exit':
            break
        
        if search_input:
            search_results = checker.search_conflicts(search_input)
            if search_results:
                print(f"\n搜索结果 ({len(search_results)} 个冲突):")
                
                for i, conflict in enumerate(search_results, 1):
                    print(f"\n冲突 #{i}:")
                    print(f"MOD 1: {Fore.YELLOW}{conflict['mod1']}{Fore.RESET}")
                    print(f"MOD 2: {Fore.YELLOW}{conflict['mod2']}{Fore.RESET}")
                    print("冲突的hash值及文件路径:")
                    for detail in conflict['details']:
                        print(f"  Hash: {Fore.GREEN}{detail['hash']}{Fore.RESET}")
                        print(f"  文件1: {Fore.CYAN}{detail['file1']}{Fore.RESET}")
                        print(f"  文件2: {Fore.CYAN}{detail['file2']}{Fore.RESET}")
            else:
                print(f"{Fore.YELLOW}未找到匹配的冲突{Fore.RESET}")
        
        print("\n输入下一个搜索关键词，或输入 'exit' 退出搜索:")
    
    # 添加暂停，防止窗口自动关闭
    input("\n按回车键退出程序...")

if __name__ == "__main__":
    main()