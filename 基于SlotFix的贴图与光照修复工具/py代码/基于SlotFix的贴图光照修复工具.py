try:
    from colorama import Fore, Back, init
except ImportError:
    import subprocess, sys, os
    print("未检测到 colorama 库，正在自动安装...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "colorama"])
    print("colorama 安装完成，正在重新运行脚本...")
    os.execl(sys.executable, sys.executable, *sys.argv)

import sys
import os
import shutil

def generate_unique_backup_filename(f):
    base, ext = os.path.splitext(os.path.basename(f))
    backup_dir = os.path.dirname(f)
    i = 1
    backup_filename = f"disabled_beifen_{base}.ini"
    backup_filepath = os.path.join(backup_dir, backup_filename)
    
    while os.path.exists(backup_filepath):
        backup_filename = f"disabled_beifen_{base}_{i}.ini"
        backup_filepath = os.path.join(backup_dir, backup_filename)
        i += 1
    
    return backup_filepath

def list_all_files_and_dirs(directory):
    all_files_and_dirs = []
    ini_files = []
    for root, dirs, files in os.walk(directory):
        # 跳过包含 'SlotFix' 的目录（不区分大小写）
        dirs[:] = [d for d in dirs 
                  if 'slotfix' not in d.lower() and 'rabbitfx' not in d.lower()]
        for file in files:
            full_path = os.path.join(root, file)
            all_files_and_dirs.append(full_path)
            # 跳过 SlotFix.ini 和 RabbitFX.ini，以及文件名中包含 'SlotFix' 的文件（不区分大小写）
            if (
                file.endswith('.ini')
                and 'disabled' not in file.lower()
                and 'Materia' not in file
                and 'slotfix' not in file.lower()
                and 'RabbitFX' not in file.lower()
                and file not in ['SlotFix.ini', 'RabbitFX.ini']
            ):
                ini_files.append(full_path)
    return all_files_and_dirs, ini_files

def comment_out_if_ps_t7_block(lines):
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.strip().startswith(';'):
            i += 1
            continue
        # 处理 if ps-t7 == 1
        if 'if ps-t7 == 1' in line:
            # 记录if起点
            if_start = i
            stack = []
            else_idx = None
            endif_idx = None
            j = i
            while j < n:
                l = lines[j]
                l_strip = l.strip()
                # 进入新if，入栈
                if l_strip.startswith('if '):
                    stack.append('if')
                # 只处理最外层else
                if l_strip.startswith('else') and len(stack) == 1 and else_idx is None:
                    else_idx = j
                # 退出if，出栈
                if l_strip.startswith('endif'):
                    if stack:
                        stack.pop()
                    if len(stack) == 0:
                        endif_idx = j
                        break
                j += 1
            if else_idx is not None and endif_idx is not None:
                # 注释 if 到 else（含 if、else），以及 endif
                for k in range(if_start, else_idx + 1):
                    if not lines[k].strip().startswith(';'):
                        lines[k] = ';' + lines[k]
                if not lines[endif_idx].strip().startswith(';'):
                    lines[endif_idx] = ';' + lines[endif_idx]
                i = endif_idx + 1
                continue
        # 处理 if $censor == 0
        if 'if $censor == 0' in line:
            if_start = i
            stack = []
            else_idx = None
            endif_idx = None
            j = i
            while j < n:
                l = lines[j]
                l_strip = l.strip()
                if l_strip.startswith('if '):
                    stack.append('if')
                if l_strip.startswith('else') and len(stack) == 1 and else_idx is None:
                    else_idx = j
                if l_strip.startswith('endif'):
                    if stack:
                        stack.pop()
                    if len(stack) == 0:
                        endif_idx = j
                        break
                j += 1
            if else_idx is not None and endif_idx is not None:
                # 注释 if 行本身
                if not lines[if_start].strip().startswith(';'):
                    lines[if_start] = ';' + lines[if_start]
                # 注释 else 到 endif（含 else、endif）
                for k in range(else_idx, endif_idx + 1):
                    if not lines[k].strip().startswith(';'):
                        lines[k] = ';' + lines[k]
                i = endif_idx + 1
                continue
        i += 1
    return lines

def replace_strings_in_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            lines = file.readlines()
        lines = comment_out_if_ps_t7_block(lines)  # 先处理注释逻辑
        replaced_lines = []
        i = 0
        n = len(lines)
        ps_keys = ['ps-t3', 'ps-t4', 'ps-t5', 'ps-t6']
        while i < n:
            line = lines[i]
            replaced = False
            # 跳过已注释的行
            if line.strip().startswith(';'):
                replaced_lines.append(line)
                i += 1
                continue
            # 替换逻辑
            if any(key in line for key in ['ps-t3 =', 'ps-t3= ', 'ps-t3=']):
                line = line.replace('ps-t3 =', 'Resource\\ZZMI\\Diffuse = ref ').replace('ps-t3=', 'Resource\\ZZMI\\Diffuse = ref ')
                replaced = True
            elif any(key in line for key in ['ps-t4 =', 'ps-t4= ', 'ps-t4=']):
                line = line.replace('ps-t4 =', 'Resource\\ZZMI\\NormalMap = ref ').replace('ps-t4=', 'Resource\\ZZMI\\NormalMap = ref ')
                replaced = True
            elif any(key in line for key in ['ps-t5 =', 'ps-t5= ', 'ps-t5=']):
                line = line.replace('ps-t5 =', 'Resource\\ZZMI\\LightMap = ref ').replace('ps-t5=', 'Resource\\ZZMI\\LightMap = ref ')
                replaced = True
            elif any(key in line for key in ['ps-t6 =', 'ps-t6= ', 'ps-t6=']):
                line = line.replace('ps-t6 =', 'Resource\\ZZMI\\MaterialMap = ref ').replace('ps-t6=', 'Resource\\ZZMI\\MaterialMap = ref ')
                replaced = True
            replaced_lines.append(line)
            # 检查下一个非空且非注释行是否为新的ps-t3/4/5/6，且本行未被注释才插入run
            if replaced:
                j = i + 1
                while j < n and (lines[j].strip() == '' or lines[j].strip().startswith(';')):
                    j += 1
                if j >= n or not any(lines[j].strip().startswith(key) for key in ps_keys):
                    # 获取上一行的前导空白
                    import re
                    indent = re.match(r'^(\s*)', line).group(1)
                    replaced_lines.append(f'{indent}run = CommandList\\ZZMI\\SetTextures\n')
            i += 1
        return replaced_lines
    except (IOError, OSError) as e:
        print(f"无法读取文件 {file_path}：{e}")
        return []
    except Exception as e:
        print(f"发生未知错误：{e}")
        return []
    
def write_replaced_content_to_file(file_path, replaced_lines):
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            original_lines = file.readlines()

        if replaced_lines != original_lines:  # 检查内容是否被修改
            temp_file_path = file_path + '.tmp'
            with open(temp_file_path, 'w', encoding='utf-8-sig') as temp_file:
                temp_file.writelines(replaced_lines)

            with open(temp_file_path, 'r', encoding='utf-8-sig') as temp_file:
                temp_content = temp_file.readlines()

            with open(temp_file_path, 'w', encoding='utf-8') as temp_file:
                temp_file.writelines(temp_content)

            backup_filepath = generate_unique_backup_filename(file_path)
            shutil.copy2(file_path, backup_filepath)
            print(Fore.GREEN + Back.WHITE + f"文件 {file_path} 已备份到 {backup_filepath}。" + Fore.RESET + Back.RESET)

            shutil.move(temp_file_path, file_path)
            print(Fore.GREEN + Back.WHITE + f"文件 {file_path} 已成功修改。" + Fore.RESET + Back.RESET)
        else:
            print(Fore.YELLOW + Back.WHITE + f"文件 {file_path} 未被修改，无需备份。" + Fore.RESET + Back.RESET)
    except (IOError, OSError) as e:
        print(f"无法写入文件 {file_path}：{e}")
    except Exception as e:
        print(f"发生未知错误：{e}")

if __name__ == "__main__":
    # 兼容 exe 和 py 脚本两种情况
    if getattr(sys, 'frozen', False):
        work_dir = os.path.dirname(sys.executable)
    else:
        work_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(work_dir)
    print(f"当前工作目录已切换为：{work_dir}")

    init()

    print(Fore.MAGENTA + Back.WHITE + "重要提示:在运行此程序前，请做好备份,以免数据损坏。（工具会自动备份ini文件）" + Fore.RESET + Back.RESET)
    print(Fore.MAGENTA + Back.WHITE + "使用前请详细阅读使用说明。" + Fore.RESET + Back.RESET)
    input("按下回车键继续运行程序...")

    try:
        all_files_and_dirs, ini_files = list_all_files_and_dirs('.')
    except (IOError, OSError) as e:
        print(f"无法访问或列出INI文件：{e}")
        input("按下回车键结束程序")
        exit()
    
    if not ini_files:
        print("没有找到任何需要修改的.ini文件。")
        input("按下回车键结束程序")
        exit()

    for f in ini_files:
        try:
            replaced_lines = replace_strings_in_file(f)
            if replaced_lines:
                write_replaced_content_to_file(f, replaced_lines)
        except (IOError, OSError) as e:
            print(f"无法读取文件 {f}：{e}")
        except Exception as e:
            print(f"发生未知错误：{e}")

    input("按下回车键结束程序")
    exit()
