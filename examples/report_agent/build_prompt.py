import json


def build_prompt(template_str, experiment_json, step_json):
    """
    将 JSON 数据填充到 Markdown Prompt 模板中

    Args:
        template_str (str): 原始 Markdown 模板字符串
        experiment_json (dict): 实验层级的元数据 (标题, 总文档)
        step_json (dict): 当前要批改的步骤数据 (包含 tools)

    Returns:
        str: 填充好的完整 Prompt
    """

    # 1. 全局与步骤层面的基础替换
    # -------------------------------------------------
    prompt = template_str.replace("{{EXPERIMENT_TITLE}}", experiment_json.get("title", ""))
    prompt = template_str.replace("{{EXPERIMENT_DOC}}", experiment_json.get("content", ""))

    prompt = prompt.replace("{{STEP_INDEX}}", str(step_json.get("step_index", 1)))
    prompt = prompt.replace("{{STEP_TITLE}}", step_json.get("title", ""))
    # 获取该步骤的分数，默认为0
    prompt = prompt.replace("{{STEP_MAX_SCORE}}", str(step_json.get("score", 0)))
    prompt = prompt.replace("{{STEP_DOC}}", step_json.get("content", ""))

    # 获取工具列表
    tools = step_json.get("tools", [])
    prompt = prompt.replace("{{TOOL_COUNT}}", str(len(tools)))

    # 2. 核心逻辑：循环构建工具部分字符串
    # -------------------------------------------------
    tools_section_str = ""

    for idx, tool in enumerate(tools, 1):
        # 提取基础信息
        tool_name = tool.get("name", "Unknown Tool")
        ref_answer = tool.get("reference_answer", "无")
        grading_inst = tool.get("grading_instruction", "无")
        student_ans = tool.get("student_answer", "未填写")

        # --- 关键点：处理不同类型的证据 (Markdown文本 vs 图片链接) ---
        raw_evidence = tool.get("evidence", "")
        evidence_type = tool.get("evidence_type", "text")  # 默认为 text

        final_evidence_str = ""

        if evidence_type == "image":
            # 如果是图片，封装成 Markdown 图片格式，方便 LLM 识别
            # 也可以直接放 URL，但 ![Image](url) 语义更强
            final_evidence_str = f"![学生提交的截图]({raw_evidence})"
        elif evidence_type == "markdown" or evidence_type == "text":
            # 如果是文本，建议用引用块或代码块包裹，防止格式混乱
            # 使用 > 引用或者 ``` 包裹都可以，这里使用 >
            final_evidence_str = f"> {raw_evidence}"
        else:
            final_evidence_str = str(raw_evidence)

        # 构建单个工具的描述块
        tool_block = f"""
### 工具 {idx}: {tool_name}

* **参考答案 (Standard Answer)**: 
  {ref_answer}

* **批改说明 (Grading Instructions)**: 
  {grading_inst}

* **学生提交 (Student Answer)**: 
  {student_ans}

* **附加内容/证据 (Evidence/Images)**: 
  {final_evidence_str}
"""
        tools_section_str += tool_block

    # 3. 替换工具部分占位符
    # -------------------------------------------------
    prompt = prompt.replace("{{TOOLS_DATA_SECTION}}", tools_section_str)

    return prompt


# ==========================================
# 示例运行与完整模板
# ==========================================

if __name__ == "__main__":
    # 1. 完整的 Markdown 模板 (无省略)
    TEMPLATE = """
# Role | 角色设定

你是一位严谨的计算机实验课助教，负责批改学生的实验报告。你的任务是根据实验指导书（标准）、评分标准和学生提交的证据（文本、图片、命令行输出），对学生当前步骤的操作进行智能评判。

# Context | 实验背景

**实验名称**: {{EXPERIMENT_TITLE}}

**实验说明文档 (Markdown)**:
\"\"\"
{{EXPERIMENT_DOC}}
\"\"\"

# Current Task | 当前评判任务

你需要评判的是该实验的第 **{{STEP_INDEX}}** 步。

**步骤名称**: {{STEP_TITLE}}
**当前步骤满分**: {{STEP_MAX_SCORE}} 分
*(注意：这是该特定步骤的权重分值，不同步骤分值可能不同)*

**步骤说明文档 (Markdown)**:
\"\"\"
{{STEP_DOC}}
\"\"\"

# Student Submission & Analysis | 学生提交与参考标准

该步骤包含 {{TOOL_COUNT}} 个操作工具/环节，请逐一核对：

{{TOOLS_DATA_SECTION}}

# Evaluation Criteria | 评判标准

请遵循以下逻辑进行分析：

1. **完整性检查**：检查学生是否完成了该步骤下所有工具的操作。

2. **证据一致性**：
   * 学生的文字描述（Student Answer）是否与附加内容（Evidence，如截图、日志）一致？
   * 如果截图显示报错，但学生描述“成功”，判定为逻辑矛盾，应当扣分。

3. **合规性检查**：
   * 对照【参考答案】和【批改说明】，检查关键参数（如端口号、版本号、文件路径）是否完全匹配。

4. **容错性**：
   * 如果仅仅是输出格式略有不同但核心结果正确（如IP地址不同但都在内网段），应视为正确，除非【批改说明】严格限制。

5. **评分计算规则 (Scoring Rules) - 严格执行**：

   * **当前步骤总分上限**：**{{STEP_MAX_SCORE}}** 分。

   * **分值分配逻辑**：
     * **优先**：如果【批改说明】中明确指定了某工具的分值（例如“截图占2分”），请严格按说明打分。
     * **默认**：如果【批改说明】未提及具体分值，则采用**平均分配**原则。
       * 计算公式：`单个工具满分 = {{STEP_MAX_SCORE}} / {{TOOL_COUNT}}`。
       * 例如：若当前步骤满分是 20 分，且有 2 个工具，且未指定权重，则每个工具满分为 10 分。

   * **最终得分**：步骤总得分 = 所有工具实际得分之和（总和不得超过 {{STEP_MAX_SCORE}}）。

# Output Format | 输出格式

请**仅**输出一段纯净的 JSON 文本，不要包含 Markdown 代码块标记（如 \`\`\`json），格式如下：

{
  "step_index": {{STEP_INDEX}},
  "is_passed": true, // 该步骤整体是否通过 (true/false)
  "total_score": 0, // 该步骤实际得分（数字，不应超过 {{STEP_MAX_SCORE}}）
  "reasoning": "简短的评判理由总结，请提及扣分点（如有）...",
  "tools_evaluation": [
    {
      "tool_name": "工具名称",
      "status": "pass", // pass/fail/warning
      "score": 0, // 该工具实际得分
      "max_score_for_tool": 0, // 该工具的计算满分（便于追溯你的分配逻辑）
      "comment": "具体评语，指出哪里对或哪里错",
      "evidence_validity": "valid" // valid/invalid/missing
    }
  ],
  "suggestion": "如果失败，给学生的改进建议"
}
"""

    # 2. 模拟输入数据 (JSON)
    mock_experiment = {
        "title": "Linux 基础命令与文本处理",
        "content": "本实验旨在掌握 Linux 文件操作命令及 Vim 编辑器的基本使用..."
    }

    # 模拟一个具体的步骤 (步骤2)
    mock_step = {
        "step_index": 2,
        "title": "Vim 编辑器实战",
        "score": 15,  # 这一步满分 15 分
        "content": "使用 Vim 创建并编辑一个名为 hello.txt 的文件，内容需包含 'Hello Linux'。",
        "tools": [
            {
                "name": "Shell History Check",
                "reference_answer": "vim hello.txt",
                "grading_instruction": "检查历史记录中是否有 vim 命令调用",
                "student_answer": "我运行了 vim 命令",
                "evidence_type": "markdown",  # 类型：MD文本
                "evidence": "```bash\n 101  ls\n 102  vim hello.txt\n 103  cat hello.txt\n```"
            },
            {
                "name": "File Content Verification",
                "reference_answer": "文件内容需包含: Hello Linux",
                "grading_instruction": "截图必须清晰显示文件内容",
                "student_answer": "编辑完成，截图如下",
                "evidence_type": "image",  # 类型：图片链接
                "evidence": "[https://oss.example.com/student_uploads/vim_result_snap.png](https://oss.example.com/student_uploads/vim_result_snap.png)"
            }
        ]
    }

    # 3. 执行生成
    final_prompt = build_prompt(TEMPLATE, mock_experiment, mock_step)

    print("--- 生成的 Prompt 预览 ---")
    print(final_prompt)