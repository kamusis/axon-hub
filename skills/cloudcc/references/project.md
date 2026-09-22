# 项目管理模块

## 命令概览

```bash
cloudcc project order           [参数...]   # 查询订单-合同
cloudcc project subitem         [参数...]   # 查询合同子项+实施计划
cloudcc project early-exec-subitem [参数...] # 查询提前执行合同子项+实施计划
cloudcc project revenue         [参数...]   # 查询收入子项+收入计划
cloudcc project opportunity     [参数...]   # 查询商机管理列表（详见 opportunity.md）
cloudcc project payment-plan    [参数...]   # 查询项目收款计划
cloudcc project sign-prediction [参数...]   # 查询签单预测（详见 sign-prediction.md）
cloudcc project revenue-prediction [参数...]   # 查询收入预测（详见 revenue-prediction.md）
cloudcc project work-report     [参数...]   # 查询项目报工信息
```

**输出固定为 JSON**（面向 Agent），所有命令默认 `--output json`。

---

## 业务关系

```
合同 (1) → 订单 (N) → 项目管理 (N) → 合同子项 (N) → 实施计划 (N)
                    ↓
                   收入子项 (N) → 收入计划 (N)

提前执行合同 (1) → 项目管理 (N) → 合同子项 (N) → 实施计划 (N)
```

- `--contract-code`：合同编号，CLI 内部自动联动，无需手动查 orderId
- `--order-name`：订单编号（`dd.name` 字段），精准匹配，三个命令均支持，无需联动

---

## 查询策略（Agent 决策）

### 入参决策

| 用户提供的信息 | 推荐参数 | 适用命令 | 说明 |
|-------------|---------|---------|------|
| 合同编号（如 `HT20260001`） | `--contract-code` | order / subitem / revenue | **首选**：CLI 内部自动联动，合同→订单→数据 |
| 订单编号（如 `DD20260001`） | `--order-name` | order / subitem / revenue | 精准直查，无需联动 |
| 已有 orderId（来自 order 结果） | `--order-id` | subitem / revenue | **进阶优化**：省去联动请求，适合多步查询第 2/3 步 |
| 只有合同名称关键词 | `--contract-name` | order（第一步） | 先查 order 拿到 contractCode，再用 `--contract-code` 下钻 |

### 查全貌时的推荐步骤

```
Step 1: project order   --contract-code <编号>   → 获取订单金额、负责人、orderId
Step 2: project subitem --contract-code <编号>   → 获取合同子项、实施计划、工时
Step 3: project revenue --contract-code <编号>   → 获取收入计划、确认日期
```

> 若 Step 1 已拿到 orderId，Step 2/3 改用 `--order-id` 速度更快（省去联动请求）

---

## `project order` — 订单-合同查询

### 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--contract-code` | 合同编号（模糊匹配） | `HT20260001` |
| `--contract-name` | 合同名称（模糊匹配） | `"某科技公司"` |
| `--order-name` | 订单编号（精准匹配，`dd.name`） | `DD20260001` |
| `--year` | 订单启用年份 | `2026` |
| `--status` | 订单状态 | `已启用` |
| `--owner` | 订单负责人（模糊匹配） | `"赵六"` |
| `--owner-department` | 订单负责人部门（模糊匹配，`nvl(ddccuser.suoshubumentxt,ddccuser.sjbm)`） | `"示例部门A"` |
| `--owner-tixi` | 订单负责人体系（模糊匹配，`ddccuser.zylx`） | `"示例体系"` |
| `--owner-zhiwei-status` | 订单负责人职位状态（精准匹配，`ygda.zyzt`） | `在职` |
| `--project-manager` | 项目经理姓名（模糊匹配，`xmjlccuser.name`） | `"张三"` |
| `--project-manager-email` | 项目经理邮箱（模糊匹配，`xmjlccuser.email`） | `zhangsan@example.com` |
| `--project-manager-department` | 项目经理部门（模糊匹配，`nvl(xmjlccuser.suoshubumentxt,xmjlccuser.sjbm)`） | `"示例交付部"` |
| `--executive-director-department` | 执行总监部门（模糊匹配，`nvl(xmexccuser.suoshubumentxt,xmexccuser.sjbm)`） | `"示例总监办"` |
| `--deliver-area` | 交付区域（模糊匹配，`dd.jfqy`，枚举：`北区`/`东区`/`西区`/`南区`/`海外`） | `南区` |
| `--deliver-location` | 交付地点（模糊匹配，`dd.jfdd`） | `某区` |
| `--order-start-from` | 订单开始日期起始（`dd.poksrq >=`） | `2026-01-01` |
| `--order-start-to` | 订单开始日期截止（`dd.poksrq <=`） | `2026-12-31` |
| `--order-end-from` | 订单结束日期起始（`dd.pojsrq >=`） | `2026-01-01` |
| `--order-end-to` | 订单结束日期截止（`dd.pojsrq <=`） | `2026-12-31` |
| `--deliver-start-from` | 实际交付开始日期起始（`dd.sjjfkssj >=`） | `2026-01-01` |
| `--deliver-start-to` | 实际交付开始日期截止（`dd.sjjfkssj <=`） | `2026-12-31` |
| `--deliver-end-from` | 实际交付结束日期起始（`dd.sjjfjssj >=`） | `2026-01-01` |
| `--deliver-end-to` | 实际交付结束日期截止（`dd.sjjfjssj <=`） | `2026-12-31` |
| `--sub-item-start-from` | 子项预计开始日期起始（跨维度，`htxmfj.yjxmksj >=`） | `2026-01-01` |
| `--sub-item-start-to` | 子项预计开始日期截止（跨维度，`htxmfj.yjxmksj <=`） | `2026-12-31` |
| `--sub-item-end-from` | 子项预计结束日期起始（跨维度，`htxmfj.yjxmjssj >=`） | `2026-01-01` |
| `--sub-item-end-to` | 子项预计结束日期截止（跨维度，`htxmfj.yjxmjssj <=`） | `2026-12-31` |
| `--sub-item-type` | 合同子项类型（跨维度，模糊，枚举见 subitem 节） | `一般维保` `软件-zDataX` |
| `--sub-item-category` | 合同子项小类（跨维度，模糊） | `基本维保` |
| `--sub-item-owner` | 合同子项负责人（跨维度，模糊） | `"钱七"` |
| `--category` | 收入大类（跨维度，模糊） | `周期服务` |
| `--sub-category` | 收入小类（跨维度，模糊） | `周期-一般维保` |
| `--confirm-principle` | 收入确认原则（跨维度，模糊） | `周期确认` |
| `--plan-confirm-from` | 收入预计确认日期起始（跨维度，`srjh.zxyjqrsj >=`） | `2026-01-01` |
| `--plan-confirm-to` | 收入预计确认日期截止（跨维度，`srjh.zxyjqrsj <=`） | `2026-12-31` |
| `--page` | 页码 | `1` |
| `--page-size` | 每页条数（最大100） | `20` |

### 响应字段（关键）

数据关系：合同 (1) → 订单 (N)

```json
{
  "items": [
    {
      "contract": {
        "contractId": "contractId_xxxx",
        "contractCode": "HT20260001",
        "contractName": "2026年某公司数据库维保项目",
        "contractStartDate": "2026-01-01",
        "contractEndDate": "2026-12-31",
        "contractEnableDate": "2026-01-15",
        "contractRecordType": "e标准维保"
      },
      "orders": [
        {
          "orderId": "orderId_xxxx1",
          "orderName": "DD20260001",
          "orderStartDate": "2026-01-01",
          "orderEndDate": "2026-12-31",
          "orderEnableDate": "2026-01-15",
          "actualDeliverStart": "2026-01-01",
          "actualDeliverEnd": "2026-12-31",
          "orderStatus": "已启用",
          "orderAmount": 110000,
          "orderWgAmount": 30000,
          "orderZyAmount": 80000,
          "deliverArea": "某区",
          "deliverLocation": "某区",
          "orderOwner": "赵六",
          "orderOwnerDepartment": "示例部门A",
          "orderOwnerTixi": "示例体系",
          "orderOwnerZhiweizhuangtai": "在职",
          "projectManager": "钱七",
          "projectManagerDepartment": "示例交付部",
          "executiveDirector": "孙八",
          "executiveDirectorDepartment": "示例总监办"
        }
      ]
    }
  ],
  "total": 1, "page": 1, "pageSize": 10, "totalPages": 1
}
```

| 字段 | 含义 |
|------|------|
| **contract — 合同字段** | |
| `contract.contractId` | 合同ID |
| `contract.contractCode` | 合同编号 |
| `contract.contractName` | 合同名称 |
| `contract.contractStartDate` | 合同开始日期（ht.htksrq） |
| `contract.contractEndDate` | 合同结束日期（ht.htjsrq） |
| `contract.contractEnableDate` | 合同启用日期（ht.htqyrq） |
| `contract.contractRecordType` | 合同记录类型 |
| **orders[] — 订单字段** | |
| `orders[].orderId` | 订单内部ID（用于 subitem/revenue 精准查询） |
| `orders[].orderName` | 订单编号（dd.name） |
| `orders[].orderStartDate` | 订单开始日期（dd.poksrq） |
| `orders[].orderEndDate` | 订单结束日期（dd.pojsrq） |
| `orders[].orderEnableDate` | 订单启用日期（dd.poqyrq） |
| `orders[].actualDeliverStart` | 实际交付开始时间（dd.sjjfkssj） |
| `orders[].actualDeliverEnd` | 实际交付结束时间（dd.sjjfjssj） |
| `orders[].orderStatus` | 订单状态（已启用/未启用等） |
| `orders[].orderAmount` | 订单金额（元） |
| `orders[].orderWgAmount` | 订单外购金额（元，dd.powgje） |
| `orders[].orderZyAmount` | 订单自有金额（元，订单金额 - 外购金额，空值按 0 计算） |
| `orders[].deliverArea` | 交付区域（dd.jfqy） |
| `orders[].deliverLocation` | 交付地点（dd.jfdd） |
| **orders[] — 人员字段** | |
| `orders[].orderOwner` | 订单负责人 |
| `orders[].orderOwnerDepartment` | 订单负责人部门 |
| `orders[].orderOwnerTixi` | 订单负责人体系（ddccuser.zylx） |
| `orders[].orderOwnerZhiweizhuangtai` | 订单负责人职位状态（ygda.zyzt，在职/离职） |
| `orders[].projectManager` | 项目经理 |
| `orders[].projectManagerDepartment` | 项目经理部门 |
| `orders[].executiveDirector` | 执行总监 |
| `orders[].executiveDirectorDepartment` | 执行总监部门 |

---

## `project subitem` — 合同子项+实施计划

### 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--contract-code` | 合同编号（自动联动，内部查 orderId） | `HT20260001` |
| `--order-id` | 订单ID（精准，已知时优先使用） | `orderId_xxxx1` |
| `--order-name` | 订单编号（精准，`dd.name`） | `DD20260001` |
| `--sub-item-type` | 子项类型（模糊匹配，见下方枚举） | `一般维保` `软件-zDataX` |
| `--sub-item-category` | 子项小类（模糊） | `基本维保` `高级维保` |
| `--approval-status` | 审批状态（精准） | `审批通过` `审批中` |
| `--exec-status` | 执行状态（精准） | `进行中` `已完成` `未开始` |
| `--plan-approval-status` | 实施计划审批状态（精准） | `审批通过` |
| `--year` | 年份（子项日期重叠过滤） | `2026` |
| `--project-manager` | 项目经理姓名（模糊匹配，`xmjlccuser.name`） | `"张三"` |
| `--project-manager-email` | 项目经理邮箱（模糊匹配，`xmjlccuser.email`） | `zhangsan@example.com` |
| `--owner-department` | 订单负责人部门（模糊匹配，`nvl(ddccuser.suoshubumentxt,ddccuser.sjbm)`） | `"示例部门A"` |
| `--owner-tixi` | 订单负责人体系（模糊匹配，`ddccuser.zylx`） | `"示例体系"` |
| `--owner-zhiwei-status` | 订单负责人职位状态（精准匹配，`ygda.zyzt`） | `在职` |
| `--project-manager-department` | 项目经理部门（模糊匹配，`nvl(xmjlccuser.suoshubumentxt,xmjlccuser.sjbm)`） | `"示例交付部"` |
| `--executive-director-department` | 执行总监部门（模糊匹配，`nvl(xmexccuser.suoshubumentxt,xmexccuser.sjbm)`） | `"示例总监办"` |
| `--deliver-area` | 交付区域（模糊匹配，`dd.jfqy`，枚举：`北区`/`东区`/`西区`/`南区`/`海外`） | `南区` |
| `--deliver-location` | 交付地点（模糊匹配，`dd.jfdd`） | `某区` |
| `--order-enable-from` | 订单启用日期起始（`dd.poqyrq >=`） | `2026-01-01` |
| `--order-enable-to` | 订单启用日期截止（`dd.poqyrq <=`） | `2026-12-31` |
| `--page` / `--page-size` | 分页 | — |

### subItemType 完整枚举列表

**服务类**
```
一般维保、人天服务、驻场服务、巡检服务、单次服务、代理服务、网站分析、SQL审核服务
```

**专项类**
```
专项-其他、专项-优化、专项-安全、专项-高可用、专项-咨询服务、专项-整合升级迁移
```

**软件类**
```
软件-SQM、软件-MDB、软件-Zone、软件-zData、软件-zAIoT、软件-Uqbar、软件-DMTK
软件-zDataX、软件-MogDB、软件-云盾防护、软件-zManager、软件-Bethune X
软件-Bethune Pro、软件-Bethune X专业版、软件-云镜安全审计、软件-ZDBM：备份一体机
软件-zCloud云管平台、软件-zCloud for DBaaS、软件-zCloud for DBMP标准版
软件-MyData：MySQL数据库一体机
```

**内训类**
```
内训-其他、内训-数据库方向、内训-大数据方向、内训-操作系统方向
```

**个人认证类**
```
个人-其他、个人-PG、个人-OB、个人-达梦、个人-公开课、个人-Oracle、个人-MySQL、个人-openGauss
```

> 参数支持模糊匹配，输入关键词即可，如 `--sub-item-type 软件` 可查所有软件类子项

### 响应字段（关键）

```
{
  "items": [
    {
      "contract": {
        "contractId": "contractId_xxxx",
        "contractCode": "HT20260001",
        "contractName": "2026年某公司数据库维保项目",
        "contractStartDate": "2026-01-01",
        "contractEndDate": "2026-12-31",
        "contractEnableDate": "2026-01-15",
        "contractRecordType": "e标准维保"
      },
      "orders": [
        {
          "orderId": "orderId_xxxx1",
          "orderName": "DD20260001",
          "orderStartDate": "2026-01-01",
          "orderEndDate": "2026-12-31",
          "orderEnableDate": "2026-01-15",
          "orderStatus": "已启用",
          "orderAmount": 110000,
          "orderWgAmount": 30000,
          "orderZyAmount": 80000,
          "deliverArea": "某区",
          "deliverLocation": "某区",
          "orderOwner": "赵六",
          "projectManager": "钱七",
          "executiveDirector": "孙八",
          "projectMgmts": [
            {
              "earlyExecId": "E20260001001",
              "projectMgmtId": "P20260001001",
              "projectMgmtName": "XMGL-20260001001",
              "approvalStatus": "审批通过",
              "execStatus": "进行中",
              "subItems": [
                {
                  "subItemId": "subItemId_xxxx",
                  "subItemName": "2026年某公司数据库维保项目基本维保...",
                  "subItemCode": "HTZX-20260001001",
                  "subItemType": "一般维保",
                  "subItemCategory": "基本维保",
                  "subItemStartDate": "2026-01-01",
                  "subItemEndDate": "2026-12-31",
                  "subItemQuantity": 1,
                  "subItemEstHours": 264,
                  "subItemSla": "7x24小时支持",
                  "subItemTotalHours": 180,
                  "planApprovalStatus": "审批通过",
                  "subItemOwner": "钱七",
                  "plans": [
                    {
                      "planId": "planId_xxxx",
                      "planName": "SSJH-20260001001",
                      "planStatus": "进行中",
                      "planStartDate": "2026-01-01",
                      "planEndDate": "2026-06-30",
                      "planHours": 264,
                      "planTotalHours": 180,
                      "planOwner": "周九"
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ],
  "total": 3
}
```

| 字段 | 含义 |
|------|------|
| **contract — 合同信息** | |
| `contract.contractId` | 合同ID |
| `contract.contractCode` | 合同编号 |
| `contract.contractName` | 合同名称 |
| `contract.contractStartDate` | 合同开始日期 |
| `contract.contractEndDate` | 合同结束日期 |
| `contract.contractEnableDate` | 合同启用日期 |
| `contract.contractRecordType` | 合同记录类型 |
| **orders[] — 订单列表（1:N）** | |
| `orders[].orderId` | 订单ID |
| `orders[].orderName` | 订单编号 |
| `orders[].orderStartDate` | 订单开始日期 |
| `orders[].orderEndDate` | 订单结束日期 |
| `orders[].orderEnableDate` | 订单启用日期 |
| `orders[].actualDeliverStart` | 实际交付开始时间 |
| `orders[].actualDeliverEnd` | 实际交付结束时间 |
| `orders[].orderStatus` | 订单状态 |
| `orders[].orderAmount` | 订单金额 |
| `orders[].orderWgAmount` | 订单外购金额（元） |
| `orders[].orderZyAmount` | 订单自有金额（元） |
| `orders[].deliverArea` | 交付区域 |
| `orders[].deliverLocation` | 交付地点 |
| `orders[].orderOwner` | 订单负责人 |
| `orders[].orderOwnerDepartment` | 订单负责人部门 |
| `orders[].orderOwnerTixi` | 订单负责人体系 |
| `orders[].orderOwnerZhiweizhuangtai` | 订单负责人职位状态 |
| `orders[].projectManager` | 项目经理 |
| `orders[].projectManagerDepartment` | 项目经理部门 |
| `orders[].executiveDirector` | 执行总监 |
| `orders[].executiveDirectorDepartment` | 执行总监部门 |
| **orders[].projectMgmts[] — 项目管理列表（1:N）** | |
| `orders[].projectMgmts[].earlyExecId` | 提前执行ID |
| `orders[].projectMgmts[].projectMgmtId` | 项目管理ID |
| `orders[].projectMgmts[].projectMgmtName` | 项目管理编号 |
| `orders[].projectMgmts[].approvalStatus` | 项目子项审批状态 |
| `orders[].projectMgmts[].execStatus` | 执行状态（提前执行时自动显示为“终止”） |
| `orders[].projectMgmts[].earlyExecName` | 提前执行名称 |
| `orders[].projectMgmts[].earlyExecCode` | 提前执行编号 |
| `orders[].projectMgmts[].earlyExecStart` | 提前执行开始日期 |
| `orders[].projectMgmts[].earlyExecEnd` | 提前执行结束日期 |
| **orders[].projectMgmts[].subItems[] — 合同子项列表（1:N）** | |
| `orders[].projectMgmts[].subItems[].subItemId` | 合同子项ID |
| `orders[].projectMgmts[].subItems[].subItemName` | 合同子项名称 |
| `orders[].projectMgmts[].subItems[].subItemCode` | 合同子项编号 |
| `orders[].projectMgmts[].subItems[].subItemType` | 子项类型（一般维保/软件-xxx等） |
| `orders[].projectMgmts[].subItems[].subItemCategory` | 子项小类（基本维保/高级维保等） |
| `orders[].projectMgmts[].subItems[].subItemStartDate` | 子项开始日期 |
| `orders[].projectMgmts[].subItems[].subItemEndDate` | 子项结束日期 |
| `orders[].projectMgmts[].subItems[].subItemQuantity` | 数量 |
| `orders[].projectMgmts[].subItems[].subItemEstHours` | 预计工时（小时） |
| `orders[].projectMgmts[].subItems[].subItemSla` | SLA&交付要求 |
| `orders[].projectMgmts[].subItems[].subItemTotalHours` | 子项累计报工时长 |
| `orders[].projectMgmts[].subItems[].planApprovalStatus` | 实施计划审批状态 |
| `orders[].projectMgmts[].subItems[].subItemOwner` | 合同子项负责人 |
| **orders[].projectMgmts[].subItems[].plans[] — 实施计划列表（1:N）** | |
| `orders[].projectMgmts[].subItems[].plans[].planId` | 实施计划ID |
| `orders[].projectMgmts[].subItems[].plans[].planName` | 实施计划编号 |
| `orders[].projectMgmts[].subItems[].plans[].planStatus` | 实施计划状态 |
| `orders[].projectMgmts[].subItems[].plans[].planStartDate` | 实施计划开始日期 |
| `orders[].projectMgmts[].subItems[].plans[].planEndDate` | 实施计划结束日期 |
| `orders[].projectMgmts[].subItems[].plans[].planHours` | 实施计划工时 |
| `orders[].projectMgmts[].subItems[].plans[].planTotalHours` | 实施计划累计工时（已报工时长） |
| `orders[].projectMgmts[].subItems[].plans[].planOwner` | 实施计划负责人 |

---

## `project revenue` — 收入子项+收入计划

### 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--contract-code` | 合同编号（自动联动） | `HT20260001` |
| `--order-id` | 订单ID（精准） | `orderId_xxxx1` |
| `--order-name` | 订单编号（精准） | `DD20260001` |
| `--category` | 收入大类（模糊） | `周期服务` `里程碑服务` |
| `--sub-category` | 收入小类（模糊） | `周期-一般维保` |
| `--confirm-principle` | 确认原则（模糊） | `周期确认` `里程碑确认` |
| `--approval-status` | 审批状态（默认`审批通过`，传空查全部） | `审批通过` |
| `--year` | 收入计划年度 | `2026` |
| `--confirm-from` | 计划确认日期起始 | `2026-01-01` |
| `--confirm-to` | 计划确认日期截止 | `2026-12-31` |
| `--assess` | 是否考核项 | `true` / `false` |
| `--plan-completed` | 收入计划完成状态（精准匹配，`srjh.srsfywc`） | `已完成` |
| `--project-manager` | 项目经理姓名（模糊匹配，`xmjlccuser.name`） | `"张三"` |
| `--project-manager-email` | 项目经理邮箱（模糊匹配，`xmjlccuser.email`） | `zhangsan@example.com` |
| `--owner-department` | 订单负责人部门（模糊匹配，`nvl(ddccuser.suoshubumentxt,ddccuser.sjbm)`） | `"示例部门A"` |
| `--owner-tixi` | 订单负责人体系（模糊匹配，`ddccuser.zylx`） | `"示例体系"` |
| `--owner-zhiwei-status` | 订单负责人职位状态（精准匹配，`ygda.zyzt`） | `在职` |
| `--project-manager-department` | 项目经理部门（模糊匹配，`nvl(xmjlccuser.suoshubumentxt,xmjlccuser.sjbm)`） | `"示例交付部"` |
| `--executive-director-department` | 执行总监部门（模糊匹配，`nvl(xmexccuser.suoshubumentxt,xmexccuser.sjbm)`） | `"示例总监办"` |
| `--deliver-area` | 交付区域（模糊匹配，`dd.jfqy`，枚举：`北区`/`东区`/`西区`/`南区`/`海外`） | `南区` |
| `--deliver-location` | 交付地点（模糊匹配，`dd.jfdd`） | `某区` |
| `--order-enable-from` | 订单启用日期起始（`dd.poqyrq >=`） | `2026-01-01` |
| `--order-enable-to` | 订单启用日期截止（`dd.poqyrq <=`） | `2026-12-31` |
| `--page` / `--page-size` | 分页 | — |

> **注意**：`--approval-status` 默认为 `审批通过`，如需查询全部收入计划，传 `--approval-status ""`

```
{
  "items": [
    {
      "contract": {
        "contractId": "contractId_xxxx",
        "contractCode": "HT20260001",
        "contractName": "2026年某公司数据库维保项目",
        "contractStartDate": "2026-01-01",
        "contractEndDate": "2026-12-31",
        "contractEnableDate": "2026-01-15",
        "contractRecordType": "e标准维保"
      },
      "orders": [
        {
          "orderId": "orderId_xxxx1",
          "orderName": "DD20260001",
          "orderStartDate": "2026-01-01",
          "orderEndDate": "2026-12-31",
          "orderEnableDate": "2026-01-15",
          "orderStatus": "已启用",
          "orderAmount": 110000,
          "orderWgAmount": 30000,
          "orderZyAmount": 80000,
          "deliverArea": "某区",
          "deliverLocation": "某区",
          "orderOwner": "赵六",
          "projectManager": "钱七",
          "executiveDirector": "孙八",
          "subItems": [
            {
              "revenueSubId": "subId_xxx",
              "revenueSubName": "SRJH-20260001001",
              "revenueCategory": "周期服务",
              "revenueSubCategory": "周期-一般维保",
              "confirmPrinciple": "周期确认",
              "revenueAmount": 110000,
              "revenueAmountExclTax": 103773.58,
              "deliveryForm": "驻场服务",
              "manDayType": "高级",
              "manDays": 60.0,
              "plans": [
                {
                  "revenuePlanId": "planId_xxx",
                  "revenuePlanName": "SRQR-20260001001",
                  "planConfirmDate": "2026-07-15",
                  "planRevenueConfirmDate": "2026-06-30",
                  "planRevenueAmountExclTax": 50000.00,
                  "planPreTaxAmount": 53000.00,
                  "planPendingConfirmAmount": 0.00,
                  "isAssessItem": "false",
                  "actualConfirmedRevenueExclTax": 50000.00,
                  "revenuePlanCompleted": "已完成"
                }
              ]
            }
          ]
        }
      ]
    }
  ],
  "total": 13
}
```

| 字段 | 含义 |
|------|------|
| **contract — 合同信息** | |
| `contract.contractId` | 合同ID |
| `contract.contractCode` | 合同编号 |
| `contract.contractName` | 合同名称 |
| `contract.contractStartDate` | 合同开始日期 |
| `contract.contractEndDate` | 合同结束日期 |
| `contract.contractEnableDate` | 合同启用日期 |
| `contract.contractRecordType` | 合同记录类型 |
| **orders[] — 订单列表（1:N）** | |
| `orders[].orderId` | 订单ID |
| `orders[].orderName` | 订单编号 |
| `orders[].orderStartDate` | 订单开始日期 |
| `orders[].orderEndDate` | 订单结束日期 |
| `orders[].orderEnableDate` | 订单启用日期 |
| `orders[].actualDeliverStart` | 实际交付开始时间 |
| `orders[].actualDeliverEnd` | 实际交付结束时间 |
| `orders[].orderStatus` | 订单状态 |
| `orders[].orderAmount` | 订单金额 |
| `orders[].orderWgAmount` | 订单外购金额（元） |
| `orders[].orderZyAmount` | 订单自有金额（元） |
| `orders[].deliverArea` | 交付区域 |
| `orders[].deliverLocation` | 交付地点 |
| `orders[].orderOwner` | 订单负责人 |
| `orders[].orderOwnerDepartment` | 订单负责人部门 |
| `orders[].projectManager` | 项目经理 |
| `orders[].executiveDirector` | 执行总监 |
| **orders[].subItems[] — 收入子项列表（1:N）** | |
| `orders[].subItems[].revenueSubId` | 收入子项ID |
| `orders[].subItems[].revenueSubName` | 收入子项编号（SRJH-xxx） |
| `orders[].subItems[].revenueCategory` | 收入大类 |
| `orders[].subItems[].revenueSubCategory` | 收入小类 |
| `orders[].subItems[].confirmPrinciple` | 确认原则 |
| `orders[].subItems[].revenueAmount` | 收入金额（元） |
| `orders[].subItems[].revenueAmountExclTax` | 收入剔税金额（元） |
| `orders[].subItems[].assessCount` | 考核次数 |
| `orders[].subItems[].deliveryForm` | 交付形式 |
| `orders[].subItems[].softwareSaleForm` | 软件售卖形式 |
| `orders[].subItems[].manDayType` | 人天类型 |
| `orders[].subItems[].manDays` | 人天数 |
| `orders[].subItems[].approvalStatus` | 审批状态 |
| **orders[].subItems[].plans[] — 收入计划列表（1:N）** | |
| `orders[].subItems[].plans[].revenuePlanName` | 收入计划编号（SRQR-xxx） |
| `orders[].subItems[].plans[].planConfirmDate` | 预计确认日期 |
| `orders[].subItems[].plans[].planRevenueConfirmDate` | 计划收入确认日期 |
| `orders[].subItems[].plans[].planRevenueAmountExclTax` | 计划收入金额-剔税 |
| `orders[].subItems[].plans[].planPreTaxAmount` | 计划税前金额 |
| `orders[].subItems[].plans[].planPendingConfirmAmount` | 计划待确认金额 |
| `orders[].subItems[].plans[].isAssessItem` | 是否考核项（"true"/"false"字符串） |
| `orders[].subItems[].plans[].actualConfirmedRevenueExclTax` | 实际确认收入剔税金额（元） |
| `orders[].subItems[].plans[].revenuePlanCompleted` | 收入计划完成状态 |

---

## 常用查询示例

### 按合同编号查全貌

```
# Step1: 查订单
cloudcc project order --contract-code HT20260001

# Step2: 查合同子项+实施计划
cloudcc project subitem --contract-code HT20260001

# Step3: 查收入计划
cloudcc project revenue --contract-code HT20260001
```

### 已知订单编号直查（无需联动，最快）

```
cloudcc project subitem --order-name DD20260001
cloudcc project revenue --order-name DD20260001
```

### 已知 orderId 精准查询

```
cloudcc project subitem --order-id orderId_xxxx1
cloudcc project revenue --order-id orderId_xxxx1
```

### 按年份+状态筛选

```
cloudcc project order --year 2026 --status 已启用
cloudcc project subitem --year 2026 --exec-status 进行中
cloudcc project revenue --year 2026 --category 周期服务
```

### 查指定日期范围的收入计划

```
cloudcc project revenue --confirm-from 2026-06-01 --confirm-to 2026-06-30
```

### 按订单启用日期筛选收入

```
cloudcc project revenue --order-enable-from 2026-01-01 --order-enable-to 2026-06-30
```

### 订单日期维度筛选

```
# 按订单开始日期范围查询
cloudcc project order --order-start-from 2026-01-01 --order-start-to 2026-06-30

# 按订单结束日期范围查询
cloudcc project order --order-end-from 2026-06-01 --order-end-to 2026-12-31

# 按实际交付开始日期范围查询
cloudcc project order --deliver-start-from 2026-01-01 --deliver-start-to 2026-06-30

# 按实际交付结束日期范围查询
cloudcc project order --deliver-end-from 2025-01-01 --deliver-end-to 2025-12-31
```

### 合同子项日期维度筛选（跨维度，触发 JOIN htxmfj）

```
# 预计开始日期范围内的合同子项对应订单
cloudcc project order --sub-item-start-from 2026-01-01 --sub-item-start-to 2026-12-31

# 预计结束日期范围内的合同子项对应订单
cloudcc project order --sub-item-end-from 2026-01-01 --sub-item-end-to 2026-12-31
```

### 收入预计确认日期维度筛选（跨维度，触发 JOIN srjh）

```
# 查有 2026 年预计确认收入的订单
cloudcc project order --plan-confirm-from 2026-01-01 --plan-confirm-to 2026-12-31
```

### 查考核项

```
cloudcc project revenue --contract-code HT20260001 --assess true
```

### 按项目经理查询

```
# 按项目经理姓名查询订单
cloudcc project order --project-manager "张三"

# 按项目经理邮箱查询合同子项
cloudcc project subitem --project-manager-email zhangsan@example.com

# 按项目经理查询收入计划
cloudcc project revenue --project-manager "张三" --year 2026
```

### 按部门查询

```
# 按订单负责人部门查询订单
cloudcc project order --owner-department "示例部门A"

# 按项目经理部门查询合同子项
cloudcc project subitem --project-manager-department "交付"

# 按执行总监部门查询收入计划
cloudcc project revenue --executive-director-department "数据库"

# 组合：按交付区域+项目经理部门查询订单
cloudcc project order --deliver-area 南区 --project-manager-department "交付"
```

---

## `project payment-plan` — 项目收款查询（立体嵌套结构）

### 说明

查询收款计划及其关联的合同、订单、负责人、到款明细。
返回立体嵌套结构：合同 → 1:N 订单 → 1:N 收款计划。
数据权限按收款负责人（skjh.suoshuzy）过滤，需要 `project:paymentplan:page` 权限。

### 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--contract-name` | 合同名称（模糊匹配） | `"某科技公司"` |
| `--contract-code` | 合同编号（模糊匹配） | `HT20260001` |
| `--order-name` | 订单编号（模糊匹配） | `DD20260001` |
| `--order-desc` | 订单名称（模糊匹配） | `"某项目"` |
| `--order-enable-from` | 订单启用日期起始（`dd.poqyrq >=`） | `2026-01-01` |
| `--order-enable-to` | 订单启用日期截止（`dd.poqyrq <=`） | `2026-12-31` |
| `--owner-name` | 收款负责人姓名（模糊匹配） | `"某某"` |
| `--owner-bumen` | 收款负责人部门（模糊匹配） | `"某事业部"` |
| `--owner-tixi` | 收款负责人体系（模糊匹配） | `"某体系"` |
| `--pay-date-from` | 预计收款日期起始（`skjh.yjskrq >=`） | `2026-01-01` |
| `--pay-date-to` | 预计收款日期截止（`skjh.yjskrq <=`） | `2026-12-31` |
| `--pay-status` | 收款状态（仅允许：`收款完成` / `收款未完成`） | `收款未完成` |
| `--page` / `--page-size` | 分页 | — |

### 响应结构（嵌套）

```
{
  "items": [
    {
      "contract": {
        "htName": "2026年某公司合作项目下单框架",
        "htBh": "HT20260001"
      },
      "orders": [
        {
          "ddName": "DD20260001",
          "ddMc": "某项目-2026年某公司合作项目下单框架",
          "ddPoqyrq": "2026-06-29",
          "paymentPlans": [
            {
              "skjhId": "skjhId_xxxx",
              "skjhName": "SKJH20260001",
              "sktj": "订单金额：金额总计：¥XXXXXX.XX元...",
              "sktjdcsj": "2026-06-29",
              "fkxztj": "无",
              "xztj": null,
              "yjskrq": "2026-06-30",
              "dqysje": 500000.00,
              "sjskje": 500000.00,
              "sksfywc": "收款完成",
              "ownerName": "某某",
              "ownerBumen": "某事业部>某办事处",
              "ownerTixi": "某体系",
              "ownerZhiweizhuangtai": "在职"
            }
          ]
        }
      ]
    }
  ],
  "total": 1, "page": 1, "pageSize": 10, "totalPages": 1
}
```

| 层级 | 字段 | 含义 |
|------|------|------|
| `contract` | `htName` / `htBh` | 合同名称 / 合同编号 |
| `orders[]` | `ddName` / `ddMc` / `ddPoqyrq` | 订单编号 / 订单名称 / 订单启用日期 |
| `orders[].paymentPlans[]` | `skjhId` / `skjhName` | 收款计划ID / 收款计划编号 |
| | `sktj` | 收款条件 |
| | `sktjdcsj` | 签约收款日期（不含账期） |
| | `fkxztj` / `xztj` | 付款限制条件 / 限制条件 |
| | `yjskrq` | 预计收款日期 |
| | `dqysje` / `sjskje` | 到期应收金额 / 实际收款金额（元） |
| | `sksfywc` | 收款状态（收款完成/收款未完成） |
| | `ownerName` | 收款负责人姓名 |
| | `ownerBumen` / `ownerTixi` | 收款负责人部门 / 体系 |
| | `ownerZhiweizhuangtai` | 收款负责人职位状态（在职/离职） |

### 常用查询示例

```
# 查所有收款计划
cloudcc project payment-plan --output json

# 查某人收款计划
cloudcc project payment-plan --owner-name "某某" --output json

# 查某年收款
cloudcc project payment-plan --pay-date-from 2026-01-01 --pay-date-to 2026-12-31 --output json

# 查收款未完成的计划
cloudcc project payment-plan --pay-status 收款未完成 --output json

# 查某部门收款
cloudcc project payment-plan --owner-bumen "某事业部" --output json

# 查某合同编号的收款
cloudcc project payment-plan --contract-code HT20260001 --output json
```

---

## `project work-report` — 项目报工信息查询

查询报工明细及其关联的报工单、派工单、实施计划、项目个案、合同执行子项、订单、合同、前期执行合同（扁平化，每条报工明细一行）。
数据权限按报工单负责人（bgd.ownerid）过滤，需要 `project:workreport:page` 权限。

### 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--work-report-name` | 报工单编号（模糊匹配，bgd.name） | `2021080435987` |
| `--owner-name` | 报工负责人姓名（模糊匹配） | `"张三"` |
| `--owner-department` | 报工负责人部门（模糊匹配） | `"北区服务部"` |
| `--start-time-from` | 报工明细开始日期起始（bgdmx.kssj >=） | `2026-01-01` |
| `--start-time-to` | 报工明细开始日期截止（bgdmx.kssj <=） | `2026-12-31` |
| `--order-name` | 订单编号（模糊匹配，dd.name） | `202107207472` |
| `--order-title` | 订单名称（模糊匹配，dd.ddmc） | `"某项目"` |
| `--contract-code` | 合同编号（模糊匹配，ht.htbh） | `00026554` |
| `--contract-name` | 合同名称（模糊匹配，ht.name） | `"维保合同"` |
| `--exec-plan-code` | 实施计划编号（模糊匹配，jhxgz.name） | `20210727745` |
| `--exec-plan-name` | 实施计划名称（模糊匹配，jhxgz.zt） | `"EBS"` |
| `--case-name` | 项目个案编号/名称（模糊匹配，cloudcccase.name） | `"个案编号"` |
| `--sub-item-code` | 合同执行子项编号（模糊匹配，htxmfj.htzxbh） | `"子项编号"` |
| `--sub-item-name` | 合同执行子项名称（模糊匹配，htxmfj.name） | `"子项名称"` |
| `--approval-status` | 审批状态（默认`审批通过`，传空查全部） | `审批通过` |
| `--page` | 页码 | `1` |
| `--page-size` | 每页条数（最大200，默认200） | `200` |

### 响应字段（关键）

| 字段 | 含义 |
|------|------|
| **报工明细（bgdmx）** | |
| `workDetailName` | 报工明细编号 |
| `startTime` / `endTime` | 报工开始/结束时间 |
| `workHours` | 工时（小时） |
| `workContentDesc` | 工作内容描述 |
| **报工单（bgd）** | |
| `workReportName` | 报工单编号 |
| `workContent` | 报工内容 |
| `approvalStatus` | 审批状态 |
| **负责人（ccuser）** | |
| `ownerName` | 负责人姓名 |
| `ownerDepartment` | 负责人部门（完整层级） |
| **关联单据** | |
| `assignName` | 派工单编号（pgd.name） |
| `execPlanCode` / `execPlanName` | 实施计划编号/名称（jhxgz） |
| `projectCaseName` | 项目个案编号/名称（cloudcccase.name） |
| `contractExecSubName` / `contractExecCode` | 合同执行子项名称/合同执行编号（htxmfj） |
| `orderName` / `orderTitle` | 订单编号（dd.name）/订单名称（dd.ddmc） |
| `contractName` / `contractCode` | 合同名称/合同编号（contract） |
| `preContractName` / `preContractCode` | 前期执行合同名称/编号（tqzxht） |

### 常用查询示例

```
# 查所有审批通过的报工（默认）
cloudcc project work-report --output json

# 查某人的报工
cloudcc project work-report --owner-name "张三" --output json

# 查某部门某时间段的报工
cloudcc project work-report --owner-department "北区服务部" --start-time-from 2026-01-01 --start-time-to 2026-06-30 --output json

# 按实施计划名称查报工
cloudcc project work-report --exec-plan-name "EBS" --output json

# 按合同编号查报工
cloudcc project work-report --contract-code 00026554 --output json

# 查全部审批状态（含未通过）
cloudcc project work-report --approval-status "" --output json
```

---

## `project early-exec-subitem` — 提前执行合同子项+实施计划

### 说明

查询提前执行合同（tqzxht）下的项目管理、合同子项及其关联的实施计划。
与 `project subitem` 的区别：无订单层级，以提前执行合同为顶层。

数据关系：提前执行合同 → 1:N 项目管理 → 1:N 合同子项 → 1:N 实施计划

### 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--contract-name` | 提前执行合同名称（模糊匹配） | `"某公司"` |
| `--contract-code` | 提前执行合同编号（模糊匹配） | `TQ20260001` |
| `--sub-item-type` | 子项类型（模糊匹配） | `一般维保` |
| `--sub-item-category` | 子项小类（模糊） | `基本维保` |
| `--approval-status` | 审批状态（精准） | `审批通过` |
| `--exec-status` | 执行状态（精准） | `进行中` |
| `--plan-approval-status` | 实施计划审批状态（精准） | `审批通过` |
| `--owner-name` | 合同负责人姓名（模糊匹配） | `"张三"` |
| `--owner-department` | 合同负责人部门（模糊匹配） | `"示例部门"` |
| `--owner-tixi` | 合同负责人体系（模糊匹配） | `"示例体系"` |
| `--owner-zhiwei-status` | 合同负责人职位状态（精准） | `在职` |
| `--project-manager` | 项目经理姓名（模糊匹配） | `"李四"` |
| `--project-manager-email` | 项目经理邮箱（模糊匹配） | `lisi@example.com` |
| `--project-manager-department` | 项目经理部门（模糊匹配） | `"示例交付部"` |
| `--executive-director-department` | 执行总监部门（模糊匹配） | `"示例总监办"` |
| `--page` | 页码 | `1` |
| `--page-size` | 每页条数（最大100） | `20` |

### 响应结构（嵌套）

```json
{
  "items": [
    {
      "contract": {
        "contractId": "...",
        "contractName": "提前执行合同名称",
        "contractCode": "TQ20260001",
        "contractStartDate": "2026-01-01",
        "contractEndDate": "2026-12-31",
        "contractStatus": "执行中",
        "orderOwner": "负责人",
        "orderOwnerDepartment": "部门",
        "orderOwnerTixi": "体系",
        "orderOwnerZhiweizhuangtai": "在职"
      },
      "projectMgmts": [
        {
          "projectMgmtId": "...",
          "projectMgmtName": "项目管理名称",
          "approvalStatus": "审批通过",
          "execStatus": "进行中",
          "earlyExecName": "提前执行名称",
          "earlyExecCode": "提前执行编号",
          "earlyExecStart": "2026-01-01",
          "earlyExecEnd": "2026-06-30",
          "subItems": [
            {
              "subItemId": "...",
              "subItemName": "子项名称",
              "subItemCode": "子项编号",
              "subItemType": "维保",
              "subItemCategory": "基本维保",
              "subItemStartDate": "2026-01-01",
              "subItemEndDate": "2026-12-31",
              "subItemEstHours": 100,
              "subItemTotalHours": 50,
              "plans": [
                {
                  "planId": "...",
                  "planName": "计划名称",
                  "planStatus": "进行中",
                  "planHours": 40,
                  "planTotalHours": 50
                }
              ]
            }
          ]
        }
      ]
    }
  ],
  "total": 1, "page": 1, "pageSize": 10, "totalPages": 1
}
```

### 常用查询示例

```
# 查全部提前执行合同子项
cloudcc project early-exec-subitem --output json

# 按提前执行合同编号查
cloudcc project early-exec-subitem --contract-code TQ20260001 --output json

# 按子项类型查
cloudcc project early-exec-subitem --sub-item-type 维保 --output json

# 按合同负责人查
cloudcc project early-exec-subitem --owner-name "张三" --output json
```
