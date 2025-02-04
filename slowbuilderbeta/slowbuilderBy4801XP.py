import json
import os
import time

def load_json_file(file_path):
    """
    加载并解析 JSON 文件。

    :param file_path: JSON 文件路径
    :return: 解析后的 JSON 数据或 None
    """
    if not os.path.isfile(file_path):
        print(f"错误: 文件 '{file_path}' 不存在。请检查路径并重试。")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        print(f"JSON 解码错误: {e}")
        return None


def generate_batch_commands(data, tap_x, tap_y, tap_xs, tap_ys, output_file_path):
    """
    生成包含点击、设置和等待的批处理命令，并将其写入输出文件。

    :param data: 解析后的 JSON 数据
    :param tap_x: 点击的 X 坐标
    :param tap_y: 点击的 Y 坐标
    :param output_file_path: 输出文件路径
    """
    chunked_blocks = data.get("chunkedBlocks", [])
    namespaces = data.get("namespaces", [])

    if not namespaces:
        print("错误: 'namespaces' 列表为空。")
        return

    commands = []

    for chunk in chunked_blocks:
        start_x = chunk.get("startX", 0)
        start_z = chunk.get("startZ", 0)
        blocks = chunk.get("blocks", [])

        if not blocks:
            continue

        # 按 z 坐标分组
        blocks_grouped_by_z = {}
        for block in blocks:
            if len(block) < 5:
                print(f"警告: 块数据格式不正确: {block}。跳过此块。")
                continue

            namespace_index, special_value, dx, dy, dz = block

            # 确保索引在范围内
            if namespace_index < 0 or namespace_index >= len(namespaces):
                print(f"警告: 命名空间索引 {namespace_index} 超出范围。跳过此块。")
                continue

            namespace = namespaces[namespace_index]

            # 计算绝对坐标
            x = start_x + dx
            y = dy + 3  # 假设 y 坐标是绝对的
            z = start_z + dz

            key = (z, namespace, special_value, y)
            if key not in blocks_grouped_by_z:
                blocks_grouped_by_z[key] = []
            blocks_grouped_by_z[key].append(x)

        # 处理每个 z 分组
        for key, x_list in blocks_grouped_by_z.items():
            if not x_list:
                continue

            z, namespace, special_value, y = key
            x_list_sorted = sorted(x_list)

            # 查找连续的 x 坐标范围
            fill_commands = []
            start = x_list_sorted[0]
            end = start

            for x in x_list_sorted[1:]:
                if x == end + 1:
                    end = x
                else:
                    # 检查是否需要使用 fill 命令
                    if end - start + 1 >= 2:
                        fill_commands.append((start, end))
                    else:
                        # 使用 setblock 命令
                        for x_single in range(start, end + 1):
                            setblock_text = f"/setblock\ ~{x_single}~{y}~{z}\ {namespace}\ {special_value}"
                            setblock_command = f"adb shell am broadcast -a clipper.set -e text \"{setblock_text}\""
                            tap_command = f"adb shell input tap {tap_x} {tap_y}"
                            tap_commands = f"adb shell input tap {tap_xs} {tap_ys}"
                            commands.append(tap_command)
                            commands.append("powershell -Command 'Start-sleep -Milliseconds 400'")  # 添加等待命令
                            commands.append(tap_commands)
                            commands.append("powershell -Command 'Start-sleep -Milliseconds 100'")  # 添加等待命令
                            commands.append(tap_commands)
                            commands.append(setblock_command)
                            commands.append("adb shell input keyevent 279") #粘贴
                            commands.append("powershell -Command 'Start-Sleep -Milliseconds 800'")
                            commands.append("adb shell input keyevent 66")  # 模拟按下回车
                            commands.append("powershell -Command 'Start-Sleep -Milliseconds 100'")
                            commands.append("adb shell input keyevent 66")
                            #commands.append("choice /t 1 /d y /n >nul")  # 添加等待命令
                            #commands.append("powershell -Command 'Start-Sleep -Milliseconds 950'")
                    start = x
                    end = x
            # 添加最后一个范围
            if end - start + 1 >= 2:
                fill_commands.append((start, end))
            else:
                for x_single in range(start, end + 1):
                    setblock_text = f"/setblock\ ~{x_single}~{y}~{z}\ {namespace}\ {special_value}"
                    setblock_command = f"adb shell am broadcast -a clipper.set -e text \"{setblock_text}\""
                    tap_command = f"adb shell input tap {tap_x} {tap_y}"
                    tap_commands = f"adb shell input tap {tap_xs} {tap_ys}"
                    commands.append(tap_command)
                    commands.append("powershell -Command 'Start-sleep -Milliseconds 400'")  # 添加等待命令
                    commands.append(tap_commands)
                    commands.append("powershell -Command 'Start-sleep -Milliseconds 100'")  # 添加等待命令
                    commands.append(tap_commands)
                    commands.append(setblock_command)
                    commands.append("adb shell input keyevent 279") #粘贴
                    commands.append("powershell -Command 'Start-Sleep -Milliseconds 800'")
                    commands.append("adb shell input keyevent 66")  # 模拟按下回车
                    commands.append("powershell -Command 'Start-Sleep -Milliseconds 100'")
                    commands.append("adb shell input keyevent 66")
                    #commands.append("choice /t 1 /d y /n >nul")  # 添加等待命令
                    #commands.append("powershell -Command 'Start-Sleep -Milliseconds 950'")

            # 处理 fill 命令
            if fill_commands:
                for fill_start, fill_end in fill_commands:
                    # 构建 fill 命令
                    fill_text = f"/fill\ ~{fill_start}~{y}~{z}\ ~{fill_end}~{y}~{z}\ {namespace}\ {special_value}"
                    fill_command = f"adb shell am broadcast -a clipper.set -e text \"{fill_text}\""
                    tap_command = f"adb shell input tap {tap_x} {tap_y}"
                    tap_commands = f"adb shell input tap {tap_xs} {tap_ys}"
                    commands.append(tap_command)
                    commands.append("powershell -Command 'Start-sleep -Milliseconds 400'")  # 添加等待命令
                    commands.append(tap_commands)
                    commands.append("powershell -Command 'Start-sleep -Milliseconds 100'")  # 添加等待命令
                    commands.append(tap_commands)
                    commands.append(fill_command)
                    commands.append("adb shell input keyevent 279") #粘贴
                    commands.append("powershell -Command 'Start-Sleep -Milliseconds 400'")
                    commands.append("adb shell input keyevent 66")  # 模拟按下回车
                    commands.append("powershell -Command 'Start-Sleep -Milliseconds 100'")
                    commands.append("adb shell input keyevent 66")
                    #commands.append("choice /t 1 /d y /n >nul")  # 添加等待命令
                    #commands.append("powershell -Command 'Start-Sleep -Milliseconds 1100'")

    if not commands:
        print("没有有效的块数据可生成命令。")
        return

    # 检查输出目录是否存在，如果不存在则创建
    output_dir = os.path.dirname(output_file_path)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"已创建输出目录: {output_dir}")
        except OSError as e:
            print(f"创建输出目录失败: {e}")
            return

    # 将命令写入输出文件
    try:
        with open(output_file_path, 'w', encoding='utf-8') as out_file:
            for cmd in commands:
                out_file.write(cmd + "\n")
        print(f"成功生成 {len(commands) // 5} 条命令,Path: '{output_file_path}'。")
    except IOError as e:
        print(f"写入输出文件失败: {e}")

def main():
    print("=== JSON ====>> ADB ===")

    # 获取输入文件路径
    input_file = input("input path: ").strip()

    # 加载 JSON 数据
    data = load_json_file(input_file)
    if data is None:
        return

    # 获取输出文件路径
    output_file = input("output path: ").strip()

    # 获取点击坐标
    while True:
        try:
            tap_x = int(input("请输入进入聊天栏控件的 X 坐标: ").strip())
            tap_y = int(input("请输入进入聊天栏控件的 Y 坐标: ").strip())
            tap_xs = int(input("请输入输入框的 X 坐标: ").strip())
            tap_ys = int(input("请输入输入框的 Y 坐标: ").strip())
            break
        except ValueError:
            print("请输入有效的整数坐标。")

    # 生成批处理命令
    generate_batch_commands(data, tap_x, tap_y,tap_xs,tap_ys, output_file)

    print("\nby:4801XP&梅")

if __name__ == "__main__":
    main()