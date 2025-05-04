#!/usr/bin/env python3
# 简单的MongoDB数据库备份脚本

import os
import json
import datetime
from pymongo import MongoClient

# 项目根目录和备份目录
PROJECT_ROOT = '/home/ks/Desktop/project/test_llm'
BACKUP_DIR = os.path.join(PROJECT_ROOT, 'mongodb_backup')

# 确保备份目录存在
os.makedirs(BACKUP_DIR, exist_ok=True)

# 连接到MongoDB
try:
    client = MongoClient('mongodb://localhost:27018/')
    db = client['rag_evaluation']
    
    # 获取所有集合
    collections = db.list_collection_names()
    
    print(f"开始备份数据库 rag_evaluation ({len(collections)} 个集合)")
    
    # 备份每个集合
    for collection_name in collections:
        collection = db[collection_name]
        
        # 创建集合目录
        collection_dir = os.path.join(BACKUP_DIR, collection_name)
        os.makedirs(collection_dir, exist_ok=True)
        
        # 查询所有文档
        documents = list(collection.find())
        doc_count = len(documents)
        
        # 将ObjectId转换为字符串以便JSON序列化
        for doc in documents:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
        
        # 保存到JSON文件
        backup_file = os.path.join(collection_dir, f"{collection_name}.json")
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=2)
        
        print(f"已备份集合 {collection_name}: {doc_count} 个文档")
    
    # 创建备份信息文件
    backup_info = {
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'collections': collections,
        'collection_counts': {name: len(list(db[name].find())) for name in collections}
    }
    
    with open(os.path.join(BACKUP_DIR, 'backup_info.json'), 'w', encoding='utf-8') as f:
        json.dump(backup_info, f, ensure_ascii=False, indent=2)
    
    print(f"\n数据库备份完成: {BACKUP_DIR}")
    print(f"总共备份了 {len(collections)} 个集合")
    print(f"备份时间: {backup_info['timestamp']}")
    
except Exception as e:
    print(f"备份过程中出错: {e}")
