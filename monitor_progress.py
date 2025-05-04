#!/usr/bin/env python3
# 简单的测试进度监视器，每10秒刷新一次

import os
import re
import time
import datetime
from pymongo import MongoClient

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

def clear_screen():
    """清除控制台屏幕"""
    os.system('clear')

def connect_to_db():
    """连接到MongoDB数据库"""
    try:
        client = MongoClient('mongodb://localhost:27018/')
        return client['rag_evaluation']
    except Exception as e:
        print(f"数据库连接错误: {e}")
        return None

def get_status_emoji(llm_count, eval_count):
    """根据数量获取状态emoji"""
    if eval_count >= 20:
        return "✅ Complete"
    elif llm_count >= 25:
        return "⏳ Ready for Eval"
    else:
        return "⏳ In Progress"

def get_db_count(db, test_type, model, check_type):
    """获取数据库中的条目数量"""
    try:
        collection = db[test_type]
        safe_model_name = model.replace(':', '_').replace('.', '_')
        
        if check_type == 'llm_answer':
            field_name = f"llm_answer_{safe_model_name}"
        else:
            # 针对不同测试类型的评估字段
            eval_field_prefix = {
                'bias_tests': 'bias_score',
                'contextual_relevancy_tests': 'contextual_relevancy_score',
                'faithfulness_tests': 'faithfulness_score',
                'hallucination_tests': 'hallucination_score',
                'summarization_tests': 'summarization_score',
                'toxicity_tests': 'toxicity_score'
            }
            field_prefix = eval_field_prefix.get(test_type, 'score')
            field_name = f"{field_prefix}_{safe_model_name}"
        
        count = collection.count_documents({field_name: {"$exists": True, "$ne": ""}})
        return count
    except Exception as e:
        print(f"数据库查询错误 ({test_type}/{model}/{check_type}): {e}")
        return 0

def get_current_test_info():
    """从进程列表中获取当前正在运行的测试信息"""
    try:
        # 检查正在运行的Python进程
        import subprocess
        result = subprocess.run("ps aux | grep python | grep -v grep", shell=True, capture_output=True, text=True)
        
        # 提取关键信息
        current_info = "无法确定当前运行状态"
        for line in result.stdout.splitlines():
            if "f_query_llm_answer_" in line:
                match = re.search(r'f_query_llm_answer_(\w+)\.py', line)
                if match:
                    test_type = match.group(1)
                    return f"正在查询: {test_type}"
            elif "test_" in line and "_final.py" in line:
                match = re.search(r'test_(\w+)_final\.py', line)
                if match:
                    test_type = match.group(1)
                    return f"正在评估: {test_type}"
        return current_info
    except Exception as e:
        return f"获取进程信息错误: {e}"

def show_progress():
    """显示测试进度"""
    try:
        db = connect_to_db()
        
        while True:
            try:
                clear_screen()
                now = datetime.datetime.now()
                print(f"=== LLM测试进度监视器 (更新时间: {now.strftime('%Y-%m-%d %H:%M:%S')}) ===\n")
                
                current_activity = get_current_test_info()
                print(f"当前活动: {current_activity}\n")
                
                # 全局统计
                total_tests = len(TEST_TYPES) * len(MODEL_LIST)
                complete_tests = 0
                
                print("测试进度概览:")
                print("-" * 80)
                print(f"{'测试类型':<25} {'模型':<20} {'LLM回答':<10} {'评估':<10} {'状态':<15}")
                print("-" * 80)
                
                for test_type in TEST_TYPES:
                    for model in MODEL_LIST:
                        llm_count = get_db_count(db, test_type, model, 'llm_answer')
                        eval_count = get_db_count(db, test_type, model, 'eval')
                        status = get_status_emoji(llm_count, eval_count)
                        
                        if status == "✅ Complete":
                            complete_tests += 1
                        
                        print(f"{test_type:<25} {model:<20} {llm_count:<10} {eval_count:<10} {status:<15}")
                
                # 计算完成百分比
                completion_percent = (complete_tests / total_tests) * 100 if total_tests > 0 else 0
                
                print("-" * 80)
                print(f"总体进度: {complete_tests}/{total_tests} ({completion_percent:.1f}%)")
                print(f"\n按Ctrl+C退出监视器 - 将在10秒后刷新...")
                
                time.sleep(10)
            except KeyboardInterrupt:
                print("\n监视器已停止")
                break
            except Exception as e:
                print(f"刷新时出错: {e}")
                print("5秒后重试...")
                time.sleep(5)
    except Exception as e:
        print(f"启动监视器出错: {e}")
        print("请检查MongoDB连接和其他依赖项")

if __name__ == "__main__":
    show_progress()
