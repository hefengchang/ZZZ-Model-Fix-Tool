import re
import struct
import traceback
import os
import sys
from pathlib import Path

# 启用Windows终端中的ANSI转义码支持
if sys.platform == 'win32':
    os.system('')

'''
   琉音Dialy身体Blend混合重制射 v2.5
将此脚本放置在与需要混合重映射的琉音Dialy mod相同的文件夹中并运行它。
不要在不需要混合重映射的琉音Dialy mods上运行此重映射脚本。
请勿在同一琉音Dialy mod上多次运行此重新映射脚本。
'''


POSITION_HASH = 'ff36809b'
OLD_VGX = [18, 19, 20, 54, 55, 56, 57, 58, 59, 60, 61, 62, 69, 70, 71, 72, 91, 92, 93, 94, 95, 96, 97, 98, 113, 114, 128, 129, 130, 131, 132, 188, 189]
NEW_VGX = [20, 18, 19, 62, 54, 55, 56, 57, 58, 59, 60, 61, 71, 72, 70, 69, 98, 91, 92, 93, 94, 95, 96, 97, 114, 113, 129, 128, 132, 130, 131, 189, 188]


def process_folder(folder_path: Path) -> list[Path]:
    ini_filepaths: list[Path] = []
    for path in folder_path.iterdir():
        if path.name.upper().startswith('DISABLED') and path.name.lower().endswith('.ini'):
            continue
        if path.name.upper().startswith('DESKTOP'):
            continue

        if path.is_dir():
            ini_filepaths.extend(process_folder(path))
        elif path.name.endswith('.ini'):
            ini_filepaths.append(path)

    return ini_filepaths

def get_blend_filepaths(ini_filepath: Path) -> list[Path]:
    ini_content = ini_filepath.read_text(encoding='utf-8')
    
    pattern = get_section_hash_pattern(POSITION_HASH)
    position_override_match = pattern.search(ini_content)
    if not position_override_match: return []
    blend_resources = get_blend_resources(ini_content, position_override_match.group(1))

    blend_filepaths: list[Path] = []
    line_pattern = re.compile(r'^\s*filename\s*=\s*(.*)\s*$', flags=re.IGNORECASE)
    for blend_resource in blend_resources:
            pattern = get_section_title_pattern(blend_resource)
            resource_section_match = pattern.search(ini_content)
            if not resource_section_match: continue

            for line in resource_section_match.group(1).splitlines():
                if line_match := line_pattern.match(line):
                    blend_filepaths.append(ini_filepath.parent / line_match.group(1))
                    break

    return blend_filepaths


def get_blend_resources(ini_content: str, commandlist: str):
    line_pattern = re.compile(r'^\s*(run|vb2)\s*=\s*(.*)\s*$', flags=re.IGNORECASE)
    resources = []

    for line in commandlist.splitlines():
        line_match = line_pattern.match(line)
        if not line_match: continue

        if line_match.group(1) == 'vb2':
            resources.append(line_match.group(2))

        elif line_match.group(1) == 'run':
            commandlist_title = line_match.group(2)
            pattern = get_section_title_pattern(commandlist_title)
            commandlist_match = pattern.search(ini_content)
            if commandlist_match:
                sub_resources = get_blend_resources(ini_content, commandlist_match.group(1))
                resources.extend(sub_resources)

    return resources

def get_blend_remap(buffer: bytes):
    new_buffer = bytearray()
    
    blend_stride = 32
    vertex_count = len(buffer)//blend_stride
    for i in range(vertex_count):
        blend_weights  = struct.unpack_from('<4f', buffer, i*blend_stride + 0)
        blend_indices  = struct.unpack_from('<4I', buffer, i*blend_stride + 16)

        new_buffer.extend(struct.pack('<4f4I', *blend_weights, *[
            vgx if vgx not in OLD_VGX
            else NEW_VGX[OLD_VGX.index(vgx)]
            for vgx in blend_indices
        ]))
    
    return new_buffer

def get_section_hash_pattern(hash) -> re.Pattern:
    return re.compile(r'^([ \t]*?\[(?:Texture|Shader)Override.*\][ \t]*(?:\n(?![ \t]*?\[).*?$)*?(?:\n\s*hash\s*=\s*{}[ \t]*)(?:(?:\n(?![ \t]*?\[).*?$)*(?:\n[\t ]*?[\$\w].*?$))?)\s*'.format(hash), flags=re.VERBOSE|re.IGNORECASE|re.MULTILINE)
def get_section_title_pattern(title) -> re.Pattern:
    return re.compile(r'^([ \t]*?\[{}\](?:(?:\n(?![ \t]*?\[).*?$)*(?:\n[\t ]*?[\$\w].*?$))?)\s*'.format(title), flags=re.VERBOSE|re.IGNORECASE|re.MULTILINE)

def get_backup_filepath(blend_filepath: Path):
    return (blend_filepath.parent / f'{blend_filepath.name[:-4]}.25_BACKUP.buf')
def get_marker_filepath(blend_filepath: Path):
    return (blend_filepath.parent / f'{blend_filepath.name[:-4]}.25_REMAP_APPLIED.empty')


def main():
    print('文件路径: {}'.format(Path('.').absolute()))
    print('琉音Dialy身体Blend混合重制射 v2.5')
    print()

    blend_filepaths: list[Path] = []
    for ini_filepath in process_folder(Path('.')):
        try:
            blend_filepaths.extend(get_blend_filepaths(ini_filepath))
        except:
            traceback.print_exc()
            print(f'\n解析失败 "{ini_filepath}". 终止')
            return
    blend_filepaths = sorted(set(blend_filepaths))

    if len(blend_filepaths) == 0:
        print('未找到任何匹配的混合缓冲区进行重新映射.退出.')
        return

    print('找到要重新映射的混合文件：')
    blend_data: list[tuple[Path, bytes, bytearray]] = []
    for blend_filepath in blend_filepaths:
        print(f'- "{blend_filepath.absolute()}"')

        backup_filepath = get_backup_filepath(blend_filepath)
        marker_filepath = get_marker_filepath(blend_filepath)
        if backup_filepath.exists() or marker_filepath.exists():
            print('混合重映射已应用于上述文件!!!您不得在同一琉音Dialyn mod上多次运行此重新映射脚本！！中止')
            return

        blend_buffer = blend_filepath.read_bytes()
        blend_remap  = get_blend_remap(blend_buffer)
        blend_data.append((blend_filepath, blend_buffer, blend_remap))

    print()
    print('不要在不需要混合重映射的琉音Dialyn mod上运行此重映射脚本!!!')
    print('不要在同一个琉音Dialyn mod上多次运行此重新映射脚本!!!')
    print('键入“\033[1;32mqueren\033[0m”,然后按Enter键将混合重映射应用于上述文件.')
    print('您已收到警告.')
    
    user_input = input()
    if user_input.lower() != 'queren':
        print(f'用户输入了 \'{user_input}\'. 终止!')
        return

    print('应用混合重映射中... ', end='')
    for blend_filepath, blend_buffer, blend_remap in blend_data:
        backup_filepath = get_backup_filepath(blend_filepath)
        marker_filepath = get_marker_filepath(blend_filepath)
        
        backup_filepath.write_bytes(blend_buffer)
        blend_filepath .write_bytes(blend_remap)
        marker_filepath.write_text('', encoding='utf-8')
    print('完成!')


if __name__ == '__main__':
    try: main()
    except Exception as x:
        print('\nError Occurred: {}\n'.format(x))
        print(traceback.format_exc())
    finally:
        input()
