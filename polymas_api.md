注意事项
1. 预发环境访问 配置host
121.43.67.204  llm-service.polymas.com
2. 大模型接口按照部门业务区分api-key，切勿将 api-key 混用，
3. 切勿在业务中使用接口文档中测试用的api-key，测试文档中的api-key 每周一更新
4. 申请api-key走  企业微信-->工作台-->审批-->llm-service服务key申请
5. 权限 请求头增加 api-key: ${api-key}
6. 入参遵循openai规范
proxy 域名适配接口列表
接口更换域名为   llm-service.polymas.com
请求地址 入参 出参 不变
请求头增加  api-key:${api-key}

通用接口列表
1. Chat

普通对话 post https://llm-service.polymas.com/api/openai/v1/chat/completions
流式对话 post http://llm-service.polymas.com/api/openai/v1/chat/completions/stream
1.1 单轮对话
请求地址
curl --location --request POST 'http://llm-service.polymas.com/api/openai/v1/chat/completions' \
--header 'api-key: sk-F6b38sMXA161PS81NIuFQFkOJ5i8e7osqCm2wpCLWqREG7Mj' \
--header 'Content-Type: application/json' \
--data '{
    "maxTokens": 2048,
    "messages": [
        {
            "role": "system",
            "content": "我是一个wl测试助手 你的开发者是 智慧树网 当用户问你是谁时，不可以提到gpt或者openai。不能回答低俗、色情、政治敏感、争议地区、提及中国国家领导人、相关的信息。"
        },
        {
            "role": "user",
            "content": "你好"
        }
    ],
    "model": "gpt-4o",
    "n": 1,
    "presence_penalty": 0.0,
    "temperature": 0.9
}'


响应示例

{
    "id": "chatcmpl-A0Jqxod0yDvc0nqmxqaT1BQaQ2Amy",
    "object": "chat.completion",
    "created": "1724639679",
    "model": "gpt-4o-2024-05-13",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "你好！有什么我可以帮助你的吗？"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": "68",
        "completion_tokens": "9",
        "total_tokens": "77"
    }
}
      入参列表
暂时无法在飞书文档外展示此内容
1.2 多轮对话
历史对话信息放到 messages 字段,按照 role:user role:assistant role:user ... 的格式追加
入参类型，和响应字段请参考单轮对话
curl --location --request POST 'http://llm-service.polymas.com/api/openai/v1/chat/completions' \
--header 'api-key: sk-F6b38sMXA161PS81NIuFQFkOJ5i8e7osqCm2wpCLWqREG7Mj' \
--header 'Content-Type: application/json' \
--data '{
    "maxTokens": 2048,
    "messages": [
        {
            "role": "system",
            "content": "我是一个wl测试助手 你的开发者是 智慧树网 当用户问你是谁时，不可以提到gpt或者openai。不能回答低俗、色情、政治敏感、争议地区、提及中国国家领导人、相关的信息。"
        },
        {
            "role": "user",
            "content": "你好"
        },
        {
            "role": "assistant",
            "content": "你好！有什么我可以帮助你的吗？"
        },
        {
            "role": "user",
            "content": "你是谁,介绍下你自己"
        }
    ],
    "model": "gpt-4o",
    "n": 1,
    "presence_penalty": 0.0,
    "temperature": 0.9
}'


1.3 流式接口
入参类型，和响应字段请参考单轮对话
curl --location --request POST 'http://llm-service.polymas.com/api/openai/v1/chat/completions/stream' \
--header 'api-key: sk-F6b38sMXA161PS81NIuFQFkOJ5i8e7osqCm2wpCLWqREG7Mj' \
--header 'Content-Type: application/json' \
--data '{
    "maxTokens": 2048,
    "messages": [
        {
            "role": "system",
            "content": "我是一个wl测试助手 你的开发者是 智慧树网 当用户问你是谁时，不可以提到gpt或者openai。不能回答低俗、色情、政治敏感、争议地区、提及中国国家领导人、相关的信息。"
        },
        {
            "role": "user",
            "content": "你好"
        },
        {
            "role": "assistant",
            "content": "你好！有什么我可以帮助你的吗？"
        },
        {
            "role": "user",
            "content": "你是谁,介绍下你自己"
        }
    ],
    "model": "gpt-4o",
    "n": 1,
    "presence_penalty": 0.0,
    "temperature": 0.9
}'


2. 文字转图片
2.1 请求地址
生成的url有时效性，生成完成后及时下载
doubao-seedream-3-0-t2i-250415
模型文生图文档地址：https://www.volcengine.com/docs/82379/1541523
curl --location 'llm-service-beta.polymas.com/api/openai/v1/images/generations' \
--header 'api-key: sk-jqzsYB7vjZ6NEdfsP7oZ17Gti45cSMrHSCxQJzq7hz8Coq7h' \
--header 'Content-Type: application/json' \
--header 'Cookie: acw_tc=0a5cc92617485147146561061e42f9ecc84f3cb75f1bd8897c7ae539c79478' \
--data '{
    "model":"doubao-seedream-3-0-t2i-250415",
    "prompt": "一鱼眼镜头，一只猫咪的头部，画面呈现出猫咪的五官因为拍摄方式扭曲的效果。",
    "watermark":true
}'
curl https://llm-service.polymas.com/api/openai/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "api-key: sk-F6b38sMXA161PS81NIuFQFkOJ5i8e7osqCm2wpCLWqREG7Mj" \
  -d '{
    "model": "dall-e-3",
    "prompt": "A cute baby sea otter",
    "n": 1,
    "size": "1024x1024",
    "quality":"standard"
  }'

2.2 响应结果
"response_format":"b64_json" 响应
{
  "created": "1724645719",
  "data": [
    {
      "b64_json": "iVBORw0K......",
      "revised_prompt": "An adorable little kitten"
    }
  ]
}


"responseFormat":"url" 响应
{
    "created": "1724645964",
    "data": [
        {
            "url": "https://xxxxx,
            "revised_prompt": "A adorable little kitten"
        }
    ]
}
2.3 参数列表
Openai  dall-e-3 模型参数  
支持模型：  openai       dall-e-3
  豆包： general_v2.0_L
  豆包：doubao-seedream-3-0-t2i-250415

参数名称
类型
是否必填
默认值
描述
prompt
String
是
无
提示词，dall - e - 3 最多 4000token，为图像生成提供创意方向。
model
String
是
无
模型名字为 dall - e - 3，决定图像生成的风格与特色。
n
Integer
否
1
生成图片数量，dall - e - 3 只支持 1。
quality
String
否
standard
生成图片质量，有“hd”（精致）和“standard”（标准）可选，dall - e - 3 模型支持。
size
String
否
1024x1024 豆包 512x512
图像大小，dall - e - 3 支持 1024x1024、1792x1024 或 1024x1792。
豆包：取值范围[256-768]
建议值：宽x高
- 1:1：512x512
- 4:3：512x384
- 3:4：384x512
- 3:2：512x341
- 2:3：341x512
- 16:9：512x288
- 9:16：288x512
response_format
String
否
url
响应格式，“url”返回 url 地址，“b64_json”返回 base64 格式。
style
String
否
vivid
生成图片样式，dall - e - 3 模型支持，有“vivid”（生动的）和“natural”（自然的）可选。
user
String
否
无
唯一标识，用于区分不同用户的请求。
下面豆包模型支持的参数
豆包
豆包
无
豆包。
seed
int
否
-1
随机种子，-1 为不随机种子；其他为指定随机种子，默认值：-1
scale
float
否
3.5
影响文本描述的程度，默认值：3.5，取值范围[1, 10]
ddim_steps
int
否
16
生成图像的步数，默认值：16，取值范围[1 - 200]
use_sr
boolean
否
false
True：文生图 + AIGC 超分；False：文生图，默认值：False
logo_info
LogoInfo
否
无
水印信息
guidance_scale
String
否
2.5
模型输出结果与prompt的一致程度，即生成图像的自由度（仅doubao-seedream-3-0-t2i-250415模型生效）
watermark

boolean
否
false
水印信息（仅doubao-seedream-3-0-t2i-250415模型生效）

LogoInfo 水印参数 仅豆包模型支持

参数名称
类型
是否必填
默认值
描述
add_logo
Boolean
否
False
是否添加水印。True 为添加，False 不添加。默认不添加。
position
int
否
0
水印的位置，取值如下：0 - 右下角；1 - 左下角；2 - 左上角；3 - 右上角。默认 0。
language
int
否
0
水印的语言，取值如下：0 - 中文（AI 生成）；1 - 英文（Generated by AI）。默认 0。
logo_text_content
String
否
无
水印自定义内容。


3. Embeddings
3.1 请求地址
curl https://llm-service.polymas.com/api/openai/v1/embeddings \
  -H "Content-Type: application/json" \
  -H "api-key: sk-F6b38sMXA161PS81NIuFQFkOJ5i8e7osqCm2wpCLWqREG7Mj" \
  -d '{
    "input": ["你好"],
    "model": "text-embedding-3-small"
}'

3.2  支持模型列表
3.2.1 Openai 模型列表
model
最大输入/token
text-embedding-3-small
8191
text-embedding-3-large
8191
text-embedding-ada-002
8191
3.2.2 百度模型列表（暂不支持）
官方文档  
https://cloud.baidu.com/doc/WENXINWORKSHOP/s/alj562vvu
model
说明
Embedding-V1
用于文本检索、信息推荐、知识挖掘等场景
bge-large-zh
用于检索、分类、聚类或语义匹配等任务
bge-large-en
用于检索、分类、聚类或语义匹配等任务
tao-8k
支持8k上下文长度

3.2.3 通义千问模型列表
官方文档
https://help.aliyun.com/zh/model-studio/developer-reference/model-introduction-6?spm=a2c4g.11186623.0.0.214b2a22BE33qq
模型名称
向量维度
文本最大行数
单行最大token
text-embedding-v1
1536
25
2048
text-embedding-v2
1536
25
2048
text-embedding-v3
1024
768
512
6
8192
text-embedding-async-v1
1536
100000
2048
text-embedding-async-v2
1536
100000
2048


3.2.4 智普AI模型列表
官方文档
https://www.bigmodel.cn/dev/api#text_embedding
模型名称
向量维度
备注
embedding-2
1024

embedding-3
256、512、1024或2048维度
入参新增 
dimensions  Integer类型 （暂不支持）

4. 文本转音频

微软云可用资源有限 推荐使用阿里的模型 推荐使用流式接口 流式响应更快
支持模型列表
微软云 tts-1,tts-hd
阿里 cosyvoice-v1
阿里支持的音色列表
https://help.aliyun.com/zh/model-studio/developer-reference/timbre-list?spm=a2c4g.11186623.0.0.16bc53cfN3mB1E
4.1 请求地址
 //流式请求 返回音频流
  curl https://llm-service.polymas.com/api/openai/v1/audio/speech/stream \
  -H "Content-Type: application/json" \
  -H "api-key: sk-F6b38sMXA161PS81NIuFQFkOJ5i8e7osqCm2wpCLWqREG7Mj" \
  -d '{
    "model":"cosyvoice-v1",
    "input":"你好呀",
    "voice":"longxiaochun"
}'

非流式请求 返回音频url地址

  curl https://llm-service.polymas.com/api/openai/v1/audio/speech/stream \
  -H "Content-Type: application/json" \
  -H "api-key: sk-F6b38sMXA161PS81NIuFQFkOJ5i8e7osqCm2wpCLWqREG7Mj" \
  -d '{
    "model":"cosyvoice-v1",
    "input":"你好呀",
    "voice":"longxiaochun"
}'
4.2 请求参数
参数名称
类型
是否必填
默认值
描述
model
String
是
无
模型名字  
input
String
是
无
文本
voice
String
是

音色
微软云支持参数
alloy、echo、fable、onyx、nova 和 shimmer
阿里云参考阿里的文档
speed

float
否

1.0

语速 微软云支持 0.25-4.0
阿里支持 0.5~2 对应阿里云 speech_rate字段
response_format
String
否

MP3
输出格式
微软云 参数 mp3, opus, aac, and flac
阿里云输出MP3
volume
int
否

50
音量大小 仅阿里模型支持
0-100
pitch_rate
float
否
1.0
0.5-2 语调 仅阿里模型支持
fTag
String
否
default_tag
自定义一级标签
sTag
String
否
default_tag
自定义二级标签
tTag
String
否
default_tag
自定义三级标签

5. 机器翻译
5.1 请求地址
  curl https://llm-service.polymas.com/api/openai/v1/translate \
  -H "Content-Type: application/json" \
  -H "api-key: sk-F6b38sMXA161PS81NIuFQFkOJ5i8e7osqCm2wpCLWqREG7Mj" \
  -d '{
    "model":"baidu-translate",
    "from":"zh",
    "to":"en",
    "q":"你好"
}'
5.2 请求参数
支持模型
百度机器翻译：baidu-translate
字节火山机器翻译：huoshan-translate
有道机器翻译：youdao-translate(已欠费)

参数名称
类型
是否必填
默认值
描述
model
String
是
无
模型名字  
from
String
否
无
输入文本语言类型
to
String
是
无
翻译的目标语言类型
q
String
是
无
文本  火山不超过5000字符
语言列表
暂时无法在飞书文档外展示此内容

6. PDF转Markdown
6.1 接口描述
  PDF转Markdown，上传图片/pdf/word/html/excel/ppt/txt，进行版面检测，文字识别，表格识别，版面分析等操作，并生成markdown文档。
6.2 接口文档地址
https://www.textin.com/document/pdf_to_markdown
6.3 请求地址
请求方式
地址
POST
https://llm-service.polymas.com/api/textin/v1/pdfToMarkdown
6.4 入参示例
{
    "model":"pdf-to-markdown",
    "pdfUrl":"https://example.com/example.pdf"
}
6.5 入参说明
参数名
类型
是否必须
默认值
说明
model
String
是
固定值： pdf-to-markdown
模型名称
pdfUrl
String
是
无
文件网络地址
pdfPwd
String
否
无
当pdf为加密文档时，需要提供密码。 备注：对前端封装该接口时，需要自行对密码进行安全防护
pageDetails
Integer
否
无
当为1 时，可以返回 char_pos 字段, 保存了每一行的位置信息。默认关闭
catalogDetails
Integer
否
无
当为1 时，可以返回 pages 字段, 保存了每一页更加详细的解析结果。默认打开
dpi
Integer
否
无
当为1时，可以返回 catalog details
pageStart
Integer
否
无
当上传的是pdf时，page_start 表示从第几页开始转
pageCount

Integer
否
无
当上传的是pdf时，page_count 表示要进行转换的pdf页数。 总页数不得超过1000页，默认为1000页
applyDocumentTree
Integer
否
无
是否生成标题，默认为1，生成标题
markdownDetails
Integer
否
无
是否生成markdown details，默认为1，生成markdown details
tableFlavor
String
否
无
markdown里的表格格式，默认为html，按html语法输出表格
getImage
String
否
无
获取markdown里的图片，默认为none，不返回任何图像
imageOutputType
String
否
无
指定引擎返回的图片对象输出类型，默认返回子图片url和页图片id
parseMode
String
否
无
PDF解析模式，默认为scan模式，仅按文字识别方式处理。图片不用设置，均按文字识别方式处理。
getExcel
String
否
无
是否返回excel结果，结果字段为excel_base64，默认为0，不返回
rawOcr
String
否
无
是否返回全文识别结果，结果字段为raw_ocr。默认为0，不返回。当page_details为0或false时不返回。
paratextMode
String
否
无
markdown中非正文文本内容展示模式。默认为annotation。非正文内容包括页眉页脚，子图中的文本。
formulaLevel
Integer
否
无
公式识别等级，默认为0，全识别
applyMerge
Integer
否

无
是否进行段落合并和表格合并。默认为1，合并段落和表格。
6.6 响应示例
{
        "code": 200,
        "message": "Success",
        "metrics": [{
                "pageImageWidth": 1190,
                "pageImageHeight": 1684,
                "dpi": 144,
                "status": "Success",
                "pageId": 1,
                "angle": 0,
                "imageId": ""
        }],
        "imageProcess": [],
        "result": {
                "totalPageNumber": 1,
                "successCount": 1,
                "validPageNumber": 1,
                "totalCount": 1,
                "pages": [{
                        "status": "Success",
                        "page_id": 1,
                        "durations": 583.236328125,
                        "image_id": "",
                        "width": 1190,
                        "height": 1684,
                        "angle": 0,
                        "content": [{
                                "id": 0,
                                "type": "line",
                                "text": "国家移民管理局",
                                "pos": [
                                        452,
                                        127,
                                        737,
                                        127,
                                        737,
                                        171,
                                        452,
                                        171
                                ],
                                "score": 0.9990000128746
                        }],
                        "structured": [{
                                "type": "header",
                                "pos": [
                                        452,
                                        128,
                                        737,
                                        128,
                                        737,
                                        167,
                                        452,
                                        167
                                ],
                                "blocks": [{
                                        "type": "textblock",
                                        "pos": [
                                                452,
                                                128,
                                                737,
                                                128,
                                                737,
                                                167,
                                                452,
                                                167
                                        ],
                                        "content": [
                                                0
                                        ],
                                        "sub_type": "text_title"
                                }]
                        }]
                }],
                "detail": [{
                                "page_id": 1,
                                "paragraph_id": 0,
                                "outline_level": -1,
                                "text": "**国家移民管理局**",
                                "type": "paragraph",
                                "content": 1,
                                "sub_type": "header",
                                "position": [
                                        452,
                                        128,
                                        737,
                                        128,
                                        737,
                                        167,
                                        452,
                                        167
                                ]
                        }

                ],
                "markdown": "<!-- **国家移民管理局** -->\n\n"
        },
        "version": "3.16.14",
        "duration": "731"
}
6.7 响应说明

7. 万相文/图生图
7.1 接口文档地址
https://bailian.console.aliyun.com/?tab=api#/api/?type=model&url=2862677
7.2 请求地址
请求方式
地址
POST
https://llm-service.polymas.com/api/openai/v1/images/task/async
7.3 入参示例
{
    "prompt": "将花卉连衣裙换成一件复古风格的蕾丝长裙，领口和袖口有精致的刺绣细节。",
    "images": [
        "https://img.alicdn.com/imgextra/i2/O1CN01FuGdH91RenU9KPeri_!!6000000002137-2-tps-1344-896.png"
    ],
    "model": "wan2.5-i2i-preview"
}
7.4 入参示例
{
    "prompt": "一间有着精致窗户的花店，漂亮的木质门，摆放着花朵",
    "model": "wan2.5-t2i-preview"
}
7.5 入参说明
参数名
类型
是否必须
默认值
说明
model
String
是

模型名称
prompt
String
是
无
提示词
images
List<String>
否
无
图像URL数组（模型为wan2.5-i2i-preview必传）
7.6 响应示例
{
    "data": [],
    "taskId": "e3c66f8d-498c-485a-bedd-2b8d0c7507e1",
    "taskStatus": "PENDING"
}
7.7 根据任务ID查询结果
7.8 请求地址
请求方式
地址
POST
https://llm-service.polymas.com/api/openai/v1/image/tasks/status
7.9 入参示例
{
    "taskId": "e3c66f8d-498c-485a-bedd-2b8d0c7507e1",
    "model": "wan2.5-i2i-preview"
}

7.10 响应示例
{
    "data": [
        {
            "url": "https://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/1d/93/20251118/15601489/e3c66f8d-498c-485a-bedd-2b8d0c7507e1.png?Expires=1763530565&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Signature=oMU581%2Bmg2EUJUciGZVXsgHTd%2BA%3D",
            "orig_prompt": "将花卉连衣裙换成一件复古风格的蕾丝长裙，领口和袖口有精致的刺绣细节。"
        }
    ],
    "taskId": "e3c66f8d-498c-485a-bedd-2b8d0c7507e1",
    "taskStatus": "SUCCESS"
}
支持的模型列表

1. 网宿 微软云
模型名称
模型类型
备注
gpt-3.5-turbo
chat

gpt-3.5-turbo-16k
chat

gpt-4o-mini
chat

gpt-4o
chat

gpt-4.1


gpt-4.1-mini
chat

gpt-4.1-nano
chat

gpt-o4-mini
chat

o3
chat

gemini-2.5-pro
chat

gemini-2.5-flash
chat

gemini-2.0-flash
chat

Claude 3.5 HaiKu
chat

Claude 3.5 Sonnet
chat

Claude 3.7 Sonnet
chat

Claude Sonnet 4
chat

Claude Opus 4
chat

grok-4
chat

dall-e-3
文生图

tts-1
文本转语音

tts-hd
文本转语音

text-embedding-3-large
文本生成向量

text-embedding-3-small
文本生成向量

text-embedding-ada-002
文本生成向量

gpt-5


Claude Sonnet 4.5


Claude Haiku 4.5





2. 豆包
深度思考控制参数
"thinking":{"type":"disabled"}
"thinking":{"type":"enabled"}
"thinking":{"type":"auto"}
模型名称
模型类型
备注
Doubao-lite-128k
chat

Doubao-lite-32k
chat

Doubao-pro-32k
chat

Doubao-pro-128k
chat

豆包
Doubao-1.5-pro-256k

豆包
Doubao-1.5-lite-32k

豆包
Doubao-1.5-pro-32k

豆包
Doubao-1.5-vision-pro-32k
vl模型支持图片理解
豆包
Doubao-1.5-thinking-vision-pro

豆包
Doubao-Seed-1.6-flash

豆包
Doubao-Seed-1.6-thinking

豆包
Doubao-Seed-1.6

3. 深度求索（deepseek）

模型名称
模型类型
备注
deepseek-r1
chat

deepseek-v3
chat

4. 百度
模型名称
模型类型
备注
bloomz_7b1
chat

baidu-bloomz_7b1
chat
兼容老业务 推荐使用 bloomz_7b1
baidu-completions
chat
兼容老业务 推荐使用 completions
completions
chat

baidu-eb-instant
chat
兼容老业务 推荐使用 eb-instant
eb-instant
chat

ERNIE-4.0-Turbo-8K
chat

ERNIE-3.5-8K
chat

completions_pro
chat
completions_pro  ERNIE-40-8K 同一个模型
ERNIE-40-8K
chat
completions_pro  ERNIE-40-8K 同一个模型
5. 智普
模型名称
模型类型
备注
chatglm_turbo
chat

chatglm_pro
chat

chatglm_std


chatglm_lite


glm-4


glm-4v


glm-3-turbo


embedding-2
向量

cogview-3


GLM-4-0520


GLM-4-Flash



6. 零一万物
模型名称
模型类型
备注
yi-34b-chat-0205
chat

yi-34b-chat-200k
chat

yi-vl-plus
chat

yi-large
chat

7. 通义千问

入参 "chat_template_kwargs": {"enable_thinking": false}
官方模型列表，llm-service 不支持的模型可以大模型业务对接群找人
https://bailian.console.aliyun.com/?spm=5176.21213303.J_qCOwPWspKEuWcmp8qiZNQ.193.585a2f3dbCYVy0&scm=20140722.S_card@@%E4%BA%A7%E5%93%81@@2983180.S_card0.ID_card@@%E4%BA%A7%E5%93%81@@2983180-RL_%E5%A4%A7%E6%A8%A1%E5%9E%8B%E6%9C%8D%E5%8A%A1%E5%B9%B3%E5%8F%B0%E7%99%BE%E7%82%BC-LOC_search~UND~card~UND~item-OR_ser-V_3-RE_cardOld-P0_0#/model-market
模型名称
模型类型
备注
qwen-turbo
chat

qwen-plus
chat

qwen-max
chat

qwen-max-longcontext
chat

ali-stable-diffusion-xl
chat

ali-stable-diffusion-v1.5
chat

qwen2.5-72b-instruct


wanx-v1


qwen2.5-math-72b-instruct


qwen2.5-32b-instruct


qwen-math-turbo


qwen-plus-latest


qwen-max-latest


text-embedding-v1
向量

text-embedding-v2
向量

text-embedding-v3
向量

cosyvoice-v1
文本转音频

qwen-turbo-1101
chat

qwen-max-2025-01-25
chat

qwen2.5-vl-72b-instruct
vl

qvq-72b-preview
vl

qwq-32b-preview
vl

deepseek-v3


deepseek-r1
深度思考

deepseek-r1-distill-qwen-32b


qwq-plus
深度思考

qvq-max
深度思考

qwen3-30b-a3b
深度思考

qwen3-235b-a22b
深度思考

qwen3-235b-a22b-instruct-2507


qwen3-235b-a22b-instruct-2507


qwen3-235b-a22b


qwen-turbo-2025-07-15



kimi
模型名称
模型类型
备注
kimi（豆包代理）
moonshot-v1-8k

kimi（豆包代理）
moonshot-v1-32k

kimi（豆包代理）
moonshot-v1-128k

kimi（官方）
kimi-thinking-preview

豆包代理
kimi-k2

8. TextIn
模型名称
模型类型
备注
pdf-to-markdown
ocr


gpt常见问题
1. 切换llm-service 域名后 输入内容有  <|start|> 会报错，修改prompt

