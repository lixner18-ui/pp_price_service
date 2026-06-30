import pandas as pd
import re
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading

class TdxConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("通达信数据转换工具")
        self.root.geometry("600x500")
        
        # 设置默认路径（保留你原本的默认路径）
        self.default_download_dir = r"D:\我\pp_quotes\downloads"
        self.default_output_dir = r"D:\我\pp_quotes\data"
        
        self.create_widgets()

    def create_widgets(self):
        # ---- 输入目录选择 ----
        frame_input = tk.Frame(self.root)
        frame_input.pack(fill="x", padx=15, pady=10)
        
        tk.Label(frame_input, text="下载目录 (TXT):", width=12, anchor="w").pack(side="left")
        self.entry_input = tk.Entry(frame_input)
        self.entry_input.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_input.insert(0, self.default_download_dir)
        tk.Button(frame_input, text="浏览...", command=self.browse_input).pack(side="right")

        # ---- 输出目录选择 ----
        frame_output = tk.Frame(self.root)
        frame_output.pack(fill="x", padx=15, pady=10)
        
        tk.Label(frame_output, text="输出目录 (CSV):", width=12, anchor="w").pack(side="left")
        self.entry_output = tk.Entry(frame_output)
        self.entry_output.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_output.insert(0, self.default_output_dir)
        tk.Button(frame_output, text="浏览...", command=self.browse_output).pack(side="right")

        # ---- 开始按钮 ----
        self.btn_start = tk.Button(self.root, text="开始转换", bg="#107c41", fg="white", font=("Helvetica", 11, "bold"), pady=5, command=self.start_process_thread)
        self.btn_start.pack(fill="x", padx=15, pady=10)

        # ---- 日志显示区域 ----
        frame_log = tk.Frame(self.root)
        frame_log.pack(fill="both", expand=True, padx=15, pady=10)
        
        tk.Label(frame_log, text="运行日志:", anchor="w").pack(fill="x")
        self.log_area = scrolledtext.ScrolledText(frame_log, wrap=tk.WORD, height=15)
        self.log_area.pack(fill="both", expand=True)

    def browse_input(self):
        directory = filedialog.askdirectory(initialdir=self.entry_input.get())
        if directory:
            self.entry_input.delete(0, tk.END)
            self.entry_input.insert(0, directory)

    def browse_output(self):
        directory = filedialog.askdirectory(initialdir=self.entry_output.get())
        if directory:
            self.entry_output.delete(0, tk.END)
            self.entry_output.insert(0, directory)

    def log(self, message):
        """向界面日志框输出信息"""
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def start_process_thread(self):
        """开启新线程处理，防止界面卡死"""
        thread = threading.Thread(target=self.process_files)
        thread.daemon = True
        thread.start()

    def process_files(self):
        # 禁用按钮防止重复点击
        self.btn_start.config(state="disabled", text="正在处理...")
        self.log_area.delete(1.0, tk.END)
        
        download_dir = Path(self.entry_input.get().strip())
        output_dir = Path(self.entry_output.get().strip())

        if not download_dir.exists():
            self.log(f"❌ 错误: 下载目录不存在 -> {download_dir}")
            self.btn_start.config(state="normal", text="开始转换")
            return

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.log(f"❌ 无法创建输出目录: {e}")
            self.btn_start.config(state="normal", text="开始转换")
            return

        txt_files = list(download_dir.glob("*.txt"))
        self.log(f"发现 {len(txt_files)} 个txt文件\n" + "="*40)

        success_count = 0
        for file_path in txt_files:
            try:
                self.log(f"处理: {file_path.name}")

                # 【修改点】直接使用 file_path.stem 保持通达信导出的名字 (如 33#000217)
                file_name_stem = file_path.stem
                output_path = output_dir / f"{file_name_stem}.csv"

                # 读取文件
                with open(file_path, 'r', encoding='gbk') as f:
                    lines = f.readlines()

                # 找到表头行
                data_start = None
                for i, line in enumerate(lines):
                    if '日期' in line and '开盘' in line:
                        data_start = i
                        break

                if data_start is None:
                    self.log("  ❌ 未找到表头行")
                    continue
                
                data_lines = lines[data_start:]
                rows = []
                for line in data_lines:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = re.split(r'\s+', line)
                    if len(parts) >= 7:
                        rows.append(parts)
                
                if len(rows) <= 1:
                    self.log("  ❌ 无有效数据行")
                    continue

                df = pd.DataFrame(rows[1:], columns=rows[0])
                output = df[['日期', '收盘']].copy()
                output['日期'] = pd.to_datetime(output['日期']).dt.strftime('%Y-%m-%d')
                output['收盘'] = pd.to_numeric(output['收盘'])
                output.columns = ['日期', 'close']
                output = output.sort_values('日期')

                # 保存 CSV
                output.to_csv(
                    output_path,
                    index=False,
                    encoding='utf-8-sig'
                )

                self.log(f"  ✅ 完成 -> {output_path.name} (条数: {len(output)})")
                success_count += 1

            except Exception as e:
                self.log(f"  ❌ 出错: {e}")

        self.log("\n" + "="*40 + f"\n全部处理完成！成功转换 {success_count}/{len(txt_files)} 个文件。")
        self.btn_start.config(state="normal", text="开始转换")
        messagebox.showinfo("提示", f"转换完成！\n成功: {success_count} 个")

if __name__ == "__main__":
    root = tk.Tk()
    app = TdxConverterGUI(root)
    root.mainloop()