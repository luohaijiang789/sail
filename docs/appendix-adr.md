# 附录：架构决策记录（ADR）

> [← 11-roadmap](11-roadmap.md)　|　[← README](../README.md)

| ADR | 决策 | 一句话理由 |
|---|---|---|
| ADR-01 | 不微服务化，模块化单体+多Worker | 第一阶段复杂度 |
| ADR-02 | CodeQL包裹编译，不重复编译 | 性能 |
| ADR-03 | 围绕ScanRun而非Celery Task | 业务正确性 |
| ADR-04 | AI只读Evidence Bundle，不实时读代码 | 架构确定性+安全 |
| ADR-05 | AI Review挂candidate不挂instance | 消除时序循环依赖 |
| ADR-06 | 两段式评分，AI只向下否决 | AI定位为排除误报 |
| ADR-07 | 三种构建模式（非降级链） | Autobuild是默认选择非降级 |
| ADR-08 | 自动识别结果持久化到source_revision | 缓存hash稳定性 |
| ADR-09 | 指纹基于符号+数据流签名 | 抗行号漂移 |
| ADR-10 | SSE+event_seq断线重连 | 长扫描进度可靠推送 |
| ADR-11 | API资产是一等产物，与漏洞平级 | 平台不只产漏洞，还产API资产库 |
| ADR-12 | CodeQL只扫漏洞（原双轮改为单轮） | API信息提取用轻量方案 |
| ADR-13 | 提取严格依赖编译成功 | 代码不完整时提取不可信 |
| ADR-14 | API安全画像四维度 | 不只看漏洞，综合判断 |
| ADR-15 | AI漏斗式验证：CodeQL广度+AI深度 | AI只做深度验证不做发现 |
| ADR-16 | API资产分两层：轻量先出+深度后补 | 轻量快速建初版，深度可选补充 |
| ADR-17 | CodeQL退回本职：只扫漏洞 | API提取不依赖CodeQL |
| ADR-18 | AI从API入口出发验证漏洞 | Java Web攻击入口是API |
| ADR-19 | NEED_MORE_CONTEXT闭环 | LLM声明缺什么，编排器补取后再问，受控多轮 |
| ADR-20 | check表：检查项矩阵 | 每个API×检查项=分级结果，含PASS/NOT_CHECKED |
| ADR-21 | 同API多检查项合并验证 | 共享上下文一次LLM，token降3-5倍 |
| ADR-22 | 增量扫描 | git diff确定变更范围，只处理受影响API |
| ADR-23 | AI分层过滤 | 小模型快速过滤，强模型深度验证 |
| ADR-24 | 自动优化反馈闭环 | 强LLM归因反馈，自动建议优化prompt/规则/白名单 |
