
###### 通用说明:
1. f_打头的文件都是final版本,其余皆是草稿.
2. test_打头的也是最终版本. 因为deepeval强制以test_开头.
3. 采用 agile+incremental 开发模式.
4. 每个文件的末尾都有注释,说明该文件的用途.
5. 像下面提到的三个文件,如果选择直接覆盖的话,功能就过多了.宁可少,不可多. 越界了. 
6. simple , simple structure,low complexity,low entropy
7. 审计的时候要做两件事情,一个是按照概括性的ai注释判断ai逻辑,另一个还没想好.
8. 这个命名规则好玩. 全部以动作打头. import/query/remove  good idea!

##### hallucination part:


###### import-halueval-data:
 f_import_halueval_data.py
1. 从本地/home/ks/Desktop/project/test_llm/qa_data.json 随机抽取20条不重复数据, 每条数据由input(提问) 和 context(文本)组成,保存到mongodb.



###### get-llm-answer:
 f_query_and_save.py
1. 从mongodb中获取question, context, _id,输出到本地ollama的llm后,将得到的llm-answer保存到mongodb  
2.  if the llm-answer already exists, skip it . 这个有必要吗? 有的,每次测试,结果都可能不一样. 很多因素都有可能变动. 覆盖很简单,但是如果数据细化就很难.


###### get-halluciation-metric-scores:
test_hallucination.py
1. 从mongodb中读取题目和llm_answer,输出到本地deepeval的halluciation-metric 评估, deepeval统一采用ollama的gemma:4B 模型
2. 如果已经测试过,跳过.  同理,这也是有必要的. 


 

##### faithfulness part


###### import-huggingface-faitheval:
https://huggingface.co/datasets/Salesforce/FaithEval-counterfactual-v1.0
1. 从huggingface读取test_case数据,保存到mongodb中的rag_evaluation db中的 faithfulness_tests文件夹,有两个key,一个是context,一个是input. 
2. 随机读取存20条,不可重复 
3. simple , simple structure,low complexity,low entropy
4. 从huggingface读数据要加proxy的
5. 有点问题,天天读很累,可以考虑拆分成两部分,先读取保存到本地,然后爆改.(可以)
6. 测试的过程中生成了很多.
所以有个问题,我们需要在后续两个模块中检测吗? 检测应读取的个数. 比如说读前20条.评估的时候也仅评估这20条.
在halluciation part,我们有限定吗
其实没什么必要的.我们已经做好了限制重复索取回复和重复评估,工作量没有增加多少. 
写三组就差不多了. 再来一组summarization 就可以去做可视化这块了.以及相关数据分析算法. 我可以去考虑了解点数据仓库/评估之类的活了. 
不过要考虑添加,多被测llm的问题了.这个时候我的数据库结构该怎么变.
do it from small. 
小公司里的自由度远大于大公司.行动阻力远小于大公司.最适合野蛮生长了.环境很重要. 

###### get-llm-answer:
 f_query_and_save.py
1. 从mongodb中获取faithfulness的问题, 输出到本地ollama的llm后,将得到的llm-answer保存到mongodb  
2.  if the llm-answer already exists, skip it . 
这个有必要吗? 有的,每次测试,结果都可能不一样. 很多因素都有可能变动. 覆盖很简单,但是如果数据细化就很难.
有必要添加数量控制吗. 添加控制永远是对的.  但是这个事情应该什么时候去做?

###### get-faithfulness-metric-scores:
test_faithfulness.py
1. 从mongodb中读取题目和llm_answer,输出到本地deepeval的faithfulness-metric 评估, deepeval统一采用ollama的gemma:4B 模型,可以参照halluciation.
2. 如果已经测试过,跳过.  同理,这也是有必要的. 
3. 还是要补充一个,不要自定义模型. 


##### summarization part


###### import summarization test case source
f_import_summarization_test_case_source.py
1. 从huggingface读取test_case数据,保存到mongodb中的rag_summarization db中的 summarization_tests文件夹,有两个key,一个是context,一个是input.    datasets import load_dataset  ds = load_dataset("EdinburghNLP/xsum")
2. 随机读取存20条,不可重复 
3. simple , simple structure,low complexity,low entropy
4. 从huggingface读数据要加proxy的. ks@ks:~$ env | grep proxy
no_proxy=localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8,172.16.0.0/12,::1
ftp_proxy=http://127.0.0.1:7890/
https_proxy=http://127.0.0.1:7890/
http_proxy=http://127.0.0.1:7890/
all_proxy=socks://127.0.0.1:7890/
6. 文件太大了得保存在本地. 除了第一次外都从本地读取. 
我艹,ai真的不会读/home/ks/Desktop/project/test_llm/config_for_cascade.md 这个文件的. 

ai似乎不怎么能读懂 metric 原型. 我是否要在需求readme中 指定好参考doc?  需要的. 



###### get-llm-answer:
 f_query_and_save.py
1. 从mongodb中获取context, _id,输出到本地ollama的llm后,将得到的llm-answer保存到mongodb  
2.  if the llm-answer already exists, skip it . 这个有必要吗? 有的,每次测试,结果都可能不一样. 很多因素都有可能变动. 覆盖很简单,但是如果数据细化就很难.


###### get-summarization-metric-scores:
test_summarization.py
1. 从mongodb中读取题目和llm_answer,输出到本地deepeval的summarization-metric 评估, deepeval统一采用ollama的gemma:4B 模型,可以参照halluciation. 2.不要自定义模型.




##### 上传到github密闭仓
