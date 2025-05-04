#!/usr/bin/env python3
# automated_testing.py - 简化版自动化LLM评估测试脚本

import os
import sys
import subprocess
import time
import re
from datetime import datetime

# 项目根目录和常量定义
PROJECT_ROOT = '/home/ks/Desktop/project/test_llm'
PROGRESS_FILE = os.path.join(PROJECT_ROOT, 'testing_progress.md')

# 测试类型
TEST_TYPES = [
    'bias_tests',
    'contextual_relevancy_tests',
    'faithfulness_tests',
    'hallucination_tests',
    'summarization_tests',
    'toxicity_tests'
]

# 模型列表
MODEL_LIST = [
    'deepseek-r1:1.5b',
    'gemma3:1b',
    'llama3.2:1b',
    'llama3.2:latest',
    'qwen3:1.7b',
    'smollm2:latest',
    'qwen2.5:3b',
    'cogito:latest'
]

# 脚本路径
QUERY_SCRIPTS = {
    'bias_tests': os.path.join(PROJECT_ROOT, 'f_', 'f_query_llm_answer_bias.py'),
    'contextual_relevancy_tests': os.path.join(PROJECT_ROOT, 'f_', 'f_query_llm_answer_contextual_relevancy.py'),
    'faithfulness_tests': os.path.join(PROJECT_ROOT, 'f_', 'f_query_llm_answer_faithfulness.py'),
    'hallucination_tests': os.path.join(PROJECT_ROOT, 'f_', 'f_query_llm_answer_halluciation.py'),
    'summarization_tests': os.path.join(PROJECT_ROOT, 'f_', 'f_query_llm_answer_summarization.py'),
    'toxicity_tests': os.path.join(PROJECT_ROOT, 'f_', 'f_query_llm_toxicity.py')
}

TEST_SCRIPTS = {
    'bias_tests': os.path.join(PROJECT_ROOT, 'deepeval_metrics', 'test_bias_final.py'),
    'contextual_relevancy_tests': os.path.join(PROJECT_ROOT, 'deepeval_metrics', 'test_contextual_relevancy_final.py'),
    'faithfulness_tests': os.path.join(PROJECT_ROOT, 'deepeval_metrics', 'test_faithfulness_final.py'),
    'hallucination_tests': os.path.join(PROJECT_ROOT, 'deepeval_metrics', 'test_Hallucination.py'),
    'summarization_tests': os.path.join(PROJECT_ROOT, 'deepeval_metrics', 'test_summarization_final.py'),
    'toxicity_tests': os.path.join(PROJECT_ROOT, 'deepeval_metrics', 'test_toxicity_final.py')
}

# 期望的数据库条目数量
EXPECTED_COUNT = 25
MIN_EVAL_COUNT = 20

# 运行命令并获取输出
def run_command(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"错误运行命令 {command}: {e}")
        print(f"错误输出: {e.stderr}")
        return None

# 检查数据库条目数量
def check_db_count(model, test_type, check_type):
    command = f"python {os.path.join(PROJECT_ROOT, 'db_check.py')} --model='{model}' --test_type='{test_type}' --check_type='{check_type}'"
    output = run_command(command)
    
    if output:
        match = re.search(r"Count: (\d+)", output)
        if match:
            return int(match.group(1))
    
    return 0

# 更新进度文件
def update_progress_file(test_type, model, llm_count, eval_count, status):
    with open(PROGRESS_FILE, 'r', encoding='utf-8') as file:
        content = file.readlines()
    
    # 寻找对应测试类型的表格
    test_section_start = None
    for i, line in enumerate(content):
        if f"### {test_type}" in line:
            test_section_start = i
            break
    
    if test_section_start is None:
        # 创建新表格
        test_index = TEST_TYPES.index(test_type) + 1
        content.append(f"\n\n### {test_index}. {test_type}\n")
        content.append("| Model | llm_answers | Evaluation | Status |\n")
        content.append("|-------|-------------|------------|--------|\n")
        model_line = f"| {model} | {llm_count} | {eval_count} | {status} |\n"
        content.append(model_line)
    else:
        # 查找是否已有该模型的行
        model_line_index = None
        for i in range(test_section_start, len(content)):
            if i < len(content) and f"| {model} |" in content[i]:
                model_line_index = i
                break
        
        if model_line_index is not None:
            # 更新现有行
            content[model_line_index] = f"| {model} | {llm_count} | {eval_count} | {status} |\n"
        else:
            # 添加新行
            for i in range(test_section_start, len(content)):
                if i < len(content) and "|------" in content[i]:
                    content.insert(i+1, f"| {model} | {llm_count} | {eval_count} | {status} |\n")
                    break
    
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as file:
        file.writelines(content)

# 设置模型
def set_model_in_config(model):
    config_path = os.path.join(PROJECT_ROOT, 'config.py')
    with open(config_path, 'r', encoding='utf-8') as file:
        content = file.readlines()
    
    for i, line in enumerate(content):
        if line.startswith("DEFAULT_MODEL"):
            content[i] = f"DEFAULT_MODEL = \"{model}\"  # Default model to use across all scripts\n"
            break
    
    with open(config_path, 'w', encoding='utf-8') as file:
        file.writelines(content)

# 主函数
def main():
    print(f"开始自动化测试 - {datetime.now()}")
    
    # 逐个测试类型进行测试
    for test_type in TEST_TYPES:
        print(f"\n处理测试类型: {test_type}")
        
        # 逐个模型进行测试
        for model in MODEL_LIST:
            print(f"\n测试模型: {model}")
            
            # 检查llm_answer数量
            llm_count = check_db_count(model, test_type, 'llm_answer')
            eval_count = check_db_count(model, test_type, 'eval')
            
            print(f"当前状态: llm_answers={llm_count}, eval={eval_count}")
            
            # 如果llm_answer数量不足，运行query脚本
            if llm_count < EXPECTED_COUNT:
                print(f"llm_answer数量不足{EXPECTED_COUNT}个，运行查询脚本")
                
                # 设置config.py中的模型
                set_model_in_config(model)
                
                # 运行查询脚本
                query_script = QUERY_SCRIPTS.get(test_type)
                if query_script and os.path.exists(query_script):
                    print(f"运行查询脚本: {query_script}")
                    run_command(f"python {query_script}")
                    time.sleep(2)  # 等待脚本执行完成
                    
                    # 重新检查数量
                    llm_count = check_db_count(model, test_type, 'llm_answer')
                    print(f"查询后的llm_answer数量: {llm_count}")
                else:
                    print(f"查询脚本不存在: {query_script}")
            
            # 如果llm_answer数量足够且eval数量不足，运行测试脚本
            if llm_count >= EXPECTED_COUNT and eval_count < MIN_EVAL_COUNT:
                print(f"llm_answer数量足够({llm_count}≥{EXPECTED_COUNT})，但eval数量不足({eval_count}<{MIN_EVAL_COUNT})，运行测试脚本")
                
                # 设置config.py中的模型
                set_model_in_config(model)
                
                # 运行测试脚本
                test_script = TEST_SCRIPTS.get(test_type)
                if test_script and os.path.exists(test_script):
                    print(f"运行测试脚本: {test_script}")
                    run_command(f"python {test_script}")
                    time.sleep(2)  # 等待脚本执行完成
                    
                    # 重新检查数量
                    eval_count = check_db_count(model, test_type, 'eval')
                    print(f"测试后的eval数量: {eval_count}")
                else:
                    print(f"测试脚本不存在: {test_script}")
            
            # 确定当前状态
            if eval_count >= MIN_EVAL_COUNT:
                status = "✅ Complete"
            elif llm_count >= EXPECTED_COUNT:
                status = "⏳ Ready for Eval"
            else:
                status = "⏳ In Progress"
            
            # 更新进度文件
            update_progress_file(test_type, model, llm_count, eval_count, status)
            print(f"已更新进度文件，当前状态: {status}")
        
        print(f"完成测试类型: {test_type}\n{'-'*50}")
    
    print(f"\n所有测试完成 - {datetime.now()}")

if __name__ == "__main__":
    main()
