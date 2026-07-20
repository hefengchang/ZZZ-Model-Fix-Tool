import sys, os, re, shutil, argparse

def get_base_dir():
	if getattr(sys, 'frozen', False):
		# Running as a PyInstaller executable
		return os.path.dirname(sys.executable)
	else:
		# Running as a normal script
		return os.path.dirname(os.path.abspath(__file__))

def fix_ini_file(file_path, stats):
	stats['scanned'] += 1
	print(f"\n正在扫描: {file_path}")

	with open(file_path, 'r', encoding='utf-8') as f:
		lines = f.readlines()

	new_lines = []
	changed = False

	for line in lines:
		original = line.rstrip('\n')
		modified_line = line

		# ps-t17 → GlowMap
		if re.match(r'^\s*ps-t17\s*=\s*resource', original, re.IGNORECASE):
			modified_line = re.sub(
				r'^\s*ps-t17\s*=\s*resource',
				r'Resource\\RabbitFX\\GlowMap = ref resource',
				original,
				flags=re.IGNORECASE
			) + '\n'
			changed = True

		# ps-t18 → FXMap
		elif re.match(r'^\s*ps-t18\s*=\s*resource', original, re.IGNORECASE):
			modified_line = re.sub(
				r'^\s*ps-t18\s*=\s*resource',
				r'Resource\\RabbitFX\\FXMap = ref resource',
				original,
				flags=re.IGNORECASE
			) + '\n'
			changed = True

		# RabbitFX entries missing "ref"
		elif re.match(r'^\s*resource\\rabbitfx\\glowmap\s*=\s*resource', original, re.IGNORECASE):
			modified_line = re.sub(
				r'^\s*resource\\rabbitfx\\glowmap\s*=\s*resource',
				r'Resource\\RabbitFX\\GlowMap = ref resource',
				original,
				flags=re.IGNORECASE
			) + '\n'
			changed = True

		elif re.match(r'^\s*resource\\rabbitfx\\fxmap\s*=\s*resource', original, re.IGNORECASE):
			modified_line = re.sub(
				r'^\s*resource\\rabbitfx\\fxmap\s*=\s*resource',
				r'Resource\\RabbitFX\\FXMap = ref resource',
				original,
				flags=re.IGNORECASE
			) + '\n'
			changed = True

		elif re.match(r'^\s*resource\\rabbitfx\\diffuse\s*=\s*resource', original, re.IGNORECASE):
			modified_line = re.sub(
				r'^\s*resource\\rabbitfx\\diffuse\s*=\s*resource',
				r'Resource\\RabbitFX\\Diffuse = ref resource',
				original,
				flags=re.IGNORECASE
			) + '\n'
			changed = True

		elif re.match(r'^\s*resource\\rabbitfx\\lightmap\s*=\s*resource', original, re.IGNORECASE):
			modified_line = re.sub(
				r'^\s*resource\\rabbitfx\\lightmap\s*=\s*resource',
				r'Resource\\RabbitFX\\Lightmap = ref resource',
				original,
				flags=re.IGNORECASE
			) + '\n'
			changed = True

		elif re.match(r'^\s*resource\\rabbitfx\\materialmap\s*=\s*resource', original, re.IGNORECASE):
			modified_line = re.sub(
				r'^\s*resource\\rabbitfx\\materialmap\s*=\s*resource',
				r'Resource\\RabbitFX\\Materialmap = ref resource',
				original,
				flags=re.IGNORECASE
			) + '\n'
			changed = True

		elif re.match(r'^\s*resource\\rabbitfx\\stockingmap\s*=\s*resource', original, re.IGNORECASE):
			modified_line = re.sub(
				r'^\s*resource\\rabbitfx\\stockingmap\s*=\s*resource',
				r'Resource\\RabbitFX\\Stockingmap = ref resource',
				original,
				flags=re.IGNORECASE
			) + '\n'
			changed = True

		if modified_line != line:
			stats['fixed'] += 1
			print(f"  - 原始内容: {original}")
			print(f"    修改后: {modified_line.rstrip()}")

		new_lines.append(modified_line)

	if changed:
		# Backup original file
		dirpath, filename = os.path.split(file_path)
		backup = os.path.join(dirpath, "DISABLED_RABBITFXBACKUP_" + filename)
		shutil.copy(file_path, backup)

		# Write modifications
		with open(file_path, 'w', encoding='utf-8') as f:
			f.writelines(new_lines)
		print(f"✔ 已修复并备份为 {backup}")

def restore_backups(path):
	restored = 0
	for dirpath, _, files in os.walk(path):
		for f in files:
			if f.lower().startswith('disabled_rabbitfxbackup_') and f.lower().endswith('.ini'):
				backup_path = os.path.join(dirpath, f)
				original_name = f[len('DISABLED_RABBITFXBACKUP_'):]
				original_path = os.path.join(dirpath, original_name)

				# Overwrite original
				shutil.move(backup_path, original_path)
				print(f"已恢复: {original_name}")
				restored += 1

	if restored == 0:
		print("未找到备份文件。")
	else:
		print(f"总共恢复: {restored} 个文件")


def scan_and_fix(root):
	stats = {'scanned': 0, 'fixed': 0}
	for dirpath, _, files in os.walk(root):
		for f in files:
			if f.lower().endswith('.ini') and not f.lower().startswith('disabled') and not f.lower().startswith('desktop'):
				fix_ini_file(os.path.join(dirpath, f), stats)

	print("\n--- 总结 ---")
	print(f"扫描的文件总数: {stats['scanned']}")
	print(f"修改的行数: {stats['fixed']}")

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("path", nargs="?", default=os.getcwd())
	parser.add_argument("--restore", action="store_true",
							help="恢复所有 DISABLED_RABBITFXBACKUP_*.ini 备份文件")
	args = parser.parse_args()

	if args.restore:
		restore_backups(args.path)
	else:
		scan_and_fix(args.path)
	
	input("\n按 Enter 键退出...")