# MyAgent开发

> 如果开始了不能继续下去，那么之前的开始就没有意义



## 学习计划

> 计划可以动态调整，但一定要执行

第一周：基础框架+多轮对话与上下文管理，支持N轮记忆

**多轮对话**

思考：

1、如何保留重要信息，精简上下文？

2、对于代码类的修改，往往几百行代码，如何保证逻辑正确？



第二周：工具调用基础及进阶（调用规范、并行调用、重试机制）

工具调用中，在判断模型是工具调用后需要将该模型工具调用返回的内容存入历史记录中进行返回，否则模型无法识别到之前的调用，







第三周：持久化记忆、语义记忆与向量检索





## LLM相关点



**Tokenization（分词）、** **上下文窗口管理（token的限制需要在工程中做）、**

**随机性控制：**

```
temperature = 0.0  → 确定性最强，每次输出相同，适合代码生成
temperature = 0.7  → 平衡创造性和准确性，适合对话
temperature = 1.0  → 最随机，适合创意写作
```



**Function Calling：LLM 调用工具的机制**

```
普通输出：
"这个函数有问题，你应该修改第15行..."

Function Calling 输出：
{
  "tool_call": {
    "name": "read_file",
    "arguments": { "path": "src/utils.ts" }
  }
}
```





## 实践出真知



### 工具调用问题

1、工具调用与返回结果之间的关联

```
实践背景：
问题：在第一次让模型调用工具时，没有将模型调用工具的那条会话记录保存到历史记录中，其中的tool_call_id被丢失，导致将工具结果返回给模型时模型无法识别这是干什么用的
调整：将模型调用工具的会话记录保存，连同工具执行结果一并返回给模型，这样模型才能关联起工具调用的上下文（通过tool_call_id进行关联）

正确调用记录：
{"model":"deepseek-v4-pro","messages":[{"role":"user","content":"现在几点了"},{"role":"assistant","content":"","reasoning_content":"用户想知道现在几点了，我需要使用 get_current_time 工具来获取当前时间。","tool_calls":[{"index":0,"id":"call_00_NEHc5PdaZY9jGrXlfr2sySJ4","type":"function","function":{"name":"get_current_time","arguments":"{}"}}]},{"role":"tool","tool_call_id":"call_00_NEHc5PdaZY9jGrXlfr2sySJ4","name":"get_current_time","content":"2026-04-28 00:05:24"}],"tools":[{"type":"function","function":{"name":"get_current_time","description":"当用户询问当前时间、日期或星期几时调用此工具","parameters":{"type":"object","properties":{},"required":[]}}},{"type":"function","function":{"name":"calculate","description":"当用户需要进行数学计算时调用此工具","parameters":{"type":"object","properties":{"expression":{"type":"string","description":"需要计算的数学表达式，只包含数字和运算符"}},"required":["expression"]}}}],"tool_choice":"auto"}

```

2、并行调用工具+重试机制

所谓并行就是将模型返回的调用工具列表进行循环处理，可以考虑通过线程的方式调用每个工具，最终返回一个结果



### 语义记忆与向量检索

简单的将对话存入数据库是线性记忆的一种方式，线性阶段会导致模型失忆，因为你的上下文总是有限制，不能把所有历史对话传给模型，所以需要选取最相关的几个内容返回给模型进行筛选处理，根据什么筛选？用户提问；如何筛选？向量数据库


### 基础Agent框架构建总结
现阶段基础框架
系统构成：
- agent 整体对话逻辑类（caht_agent.py）
  - 负责调用llm模型，在run方法中处理调用llm前后的逻辑（主要是对上下文管理器的内容进行设置，以及mcp工具的初始化）

- 模型调用类LLMClient的封装
  - 负责调用llm模型，需要考虑模型调用的超时情况
  - 如何实现流式输出？

- context_manager 上下文管理器类（context_manager.py）
  - 负责对上下文进行管理，包括对上下文进行增删改查，以及上下文的管理（比如token数量限制，token数量统计，上下文精简等）
  - 通过对信息进行持久化存储保证专属用户记忆（目前是什么都保存，该如何筛选重要信息？）
  -- 语义向量的存储（将文本转为向量，根据向量的相似度去提取最接近的文本信息发送给模型作为参考）

- mcp_config mcp工具配置类（mcp_config.py）
  - 负责对mcp工具进行配置，包括工具的名称，工具的描述，工具的参数，工具的调用方式等
  - 使用mcp需要注意与本地工具类做区分
  - 使用mcp对于读取文件的内容权限如何做动态控制？关键文件需要用户确认授权

- mcp mcp工具类（mcp.py）
  - 负责对mcp工具进行调用，包括工具的调用，工具的返回结果的处理等

- tools 工具类（tools.py）
  - 负责对工具进行调用，包括工具的调用，工具的返回结果的处理等

