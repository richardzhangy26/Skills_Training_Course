"""
测评报告可视化生成器
将JSON格式的测评结果转换为精美的HTML可视化报告

使用方法：
    python report_generator.py <json_file_path> [output_html_path]

依赖：
    pip install jinja2

可选（生成PDF）：
    pip install playwright
    playwright install chromium
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测评报告</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }

        /* 头部区域 */
        .header {
            background: #fff;
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .avatar {
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-weight: bold;
            font-size: 18px;
        }

        .header-title h1 {
            font-size: 18px;
            font-weight: 600;
            color: #1a1a1a;
        }

        .word-count {
            font-size: 13px;
            color: #4a90e2;
            margin-top: 4px;
        }

        .submit-time {
            font-size: 13px;
            color: #999;
        }

        /* 维度评分区域 */
        .score-section {
            background: #fff;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }

        .section-title {
            font-size: 16px;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 20px;
        }

        .score-content {
            display: flex;
            gap: 24px;
        }

        .radar-chart {
            flex: 1;
            min-height: 280px;
        }

        .score-details {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .total-score-card {
            background: #fafbfc;
            border-radius: 10px;
            padding: 16px 20px;
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .score-ring {
            width: 60px;
            height: 60px;
            position: relative;
        }

        .score-ring svg {
            transform: rotate(-90deg);
        }

        .score-ring .bg {
            fill: none;
            stroke: #e8ecf0;
            stroke-width: 6;
        }

        .score-ring .progress {
            fill: none;
            stroke: #4a90e2;
            stroke-width: 6;
            stroke-linecap: round;
            transition: stroke-dashoffset 0.5s ease;
        }

        .score-ring .score-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 14px;
            font-weight: 600;
            color: #1a1a1a;
        }

        .score-ring .score-text span {
            font-size: 11px;
            color: #999;
        }

        .total-score-label {
            font-size: 14px;
            color: #666;
        }

        .dimension-comments {
            flex: 1;
            background: #fafbfc;
            border-radius: 10px;
            padding: 16px 20px;
            max-height: 200px;
            overflow-y: auto;
        }

        .dimension-comments h4 {
            font-size: 13px;
            color: #666;
            margin-bottom: 12px;
        }

        .dimension-item {
            margin-bottom: 12px;
            font-size: 13px;
            line-height: 1.7;
        }

        .dimension-item strong {
            color: #1a1a1a;
        }

        .dimension-item p {
            color: #666;
            margin-top: 4px;
        }

        /* 分数卡片行 */
        .score-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }

        .score-card {
            background: #fff;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }

        .score-card-title {
            font-size: 13px;
            color: #666;
            margin-bottom: 8px;
        }

        .score-card-value {
            font-size: 28px;
            font-weight: 600;
            color: #1a1a1a;
        }

        .score-card-value span {
            font-size: 16px;
            color: #999;
            font-weight: normal;
        }

        /* 综合评语区 */
        .comment-section {
            background: #fff;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }

        .comment-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 16px;
        }

        .ai-badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            font-size: 11px;
            font-weight: 600;
            padding: 4px 8px;
            border-radius: 4px;
        }

        .comment-content {
            font-size: 14px;
            color: #444;
            line-height: 1.8;
            text-align: justify;
        }

        /* 改进建议区 */
        .suggestions-list {
            list-style: none;
        }

        .suggestions-list li {
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
            font-size: 14px;
            color: #444;
            line-height: 1.8;
        }

        .suggestion-number {
            flex-shrink: 0;
            width: 24px;
            height: 24px;
            background: #f0f5ff;
            color: #4a90e2;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 600;
        }

        /* 响应式 */
        @media (max-width: 768px) {
            .score-content {
                flex-direction: column;
            }

            .score-cards {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        /* 打印样式 */
        @media print {
            body {
                background: #fff;
            }

            .container {
                max-width: 100%;
                padding: 0;
            }

            .header, .score-section, .score-card, .comment-section {
                box-shadow: none;
                border: 1px solid #eee;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <div class="header">
            <div class="header-left">
                <div class="avatar">{{ title[:1] if title else "报" }}</div>
                <div class="header-title">
                    <h1>{{ title or "测评报告" }}</h1>
                    <div class="word-count">共 {{ word_count }} 字</div>
                </div>
            </div>
            <div class="submit-time">提交时间：{{ submit_time }}</div>
        </div>

        <!-- 维度评分 -->
        <div class="score-section">
            <h2 class="section-title">维度评分</h2>
            <div class="score-content">
                <div id="radarChart" class="radar-chart"></div>
                <div class="score-details">
                    <div class="total-score-card">
                        <div class="score-ring">
                            <svg width="60" height="60" viewBox="0 0 60 60">
                                <circle class="bg" cx="30" cy="30" r="24"/>
                                <circle class="progress" cx="30" cy="30" r="24"
                                    stroke-dasharray="{{ (total_score / full_mark) * 150.8 }} 150.8"/>
                            </svg>
                            <div class="score-text">{{ total_score }}<span>/{{ full_mark }}</span></div>
                        </div>
                        <div class="total-score-label">总得分</div>
                    </div>
                    <div class="dimension-comments">
                        <h4>维度评语</h4>
                        {% for dim in dimension_scores %}
                        <div class="dimension-item">
                            <strong>{{ dim.evaluationDimension }}：</strong>
                            <p>{{ dim.scoreReason[:150] }}{% if dim.scoreReason|length > 150 %}...{% endif %}</p>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>

        <!-- 分数卡片 -->
        <div class="score-cards">
            {% for dim in dimension_scores %}
            <div class="score-card">
                <div class="score-card-title">{{ dim.evaluationDimension }}</div>
                <div class="score-card-value">{{ dim.dimensionScore }}<span>/ {{ dim.dimensionFullMark }}</span></div>
            </div>
            {% endfor %}
        </div>

        <!-- 综合评语 -->
        <div class="comment-section">
            <div class="comment-header">
                <span class="ai-badge">AI</span>
                <h3 class="section-title" style="margin-bottom: 0;">综合评语</h3>
            </div>
            <div class="comment-content">{{ comprehensive_comment }}</div>
        </div>

        <!-- 改进建议 -->
        {% if improvement_suggestions %}
        <div class="comment-section">
            <div class="comment-header">
                <span class="ai-badge">AI</span>
                <h3 class="section-title" style="margin-bottom: 0;">改进建议</h3>
            </div>
            <ul class="suggestions-list">
                {% for suggestion in improvement_suggestions %}
                <li>
                    <span class="suggestion-number">{{ loop.index }}</span>
                    <span>{{ suggestion }}</span>
                </li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
    </div>

    <script>
        // 雷达图配置
        var radarChart = echarts.init(document.getElementById('radarChart'));

        var dimensionData = {{ dimension_data_json | safe }};

        var option = {
            radar: {
                indicator: dimensionData.map(d => ({
                    name: d.name.length > 6 ? d.name.slice(0, 6) + '...' : d.name,
                    max: d.max
                })),
                center: ['50%', '55%'],
                radius: '65%',
                axisName: {
                    color: '#666',
                    fontSize: 11
                },
                splitLine: {
                    lineStyle: {
                        color: '#e8ecf0'
                    }
                },
                splitArea: {
                    areaStyle: {
                        color: ['#fff', '#fafbfc']
                    }
                },
                axisLine: {
                    lineStyle: {
                        color: '#e8ecf0'
                    }
                }
            },
            series: [{
                type: 'radar',
                data: [{
                    value: dimensionData.map(d => d.value),
                    name: '得分',
                    areaStyle: {
                        color: 'rgba(74, 144, 226, 0.2)'
                    },
                    lineStyle: {
                        color: '#4a90e2',
                        width: 2
                    },
                    itemStyle: {
                        color: '#4a90e2'
                    }
                }]
            }]
        };

        radarChart.setOption(option);

        // 响应式
        window.addEventListener('resize', function() {
            radarChart.resize();
        });
    </script>
</body>
</html>
"""


def parse_report_data(json_file_path: str) -> dict:
    """解析JSON报告文件"""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 提取核心数据
    report_data = data.get('data', data)
    if 'artifacts' in report_data:
        artifact = report_data['artifacts'][0]
        parts = artifact.get('parts', [])
        if parts:
            core_data = parts[0].get('data', {})
        else:
            core_data = {}
    else:
        core_data = report_data

    # 格式化时间
    timestamp = report_data.get('status', {}).get('timestamp', '')
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            submit_time = dt.strftime('%Y-%m-%d %H:%M')
        except:
            submit_time = timestamp[:16].replace('T', ' ')
    else:
        submit_time = datetime.now().strftime('%Y-%m-%d %H:%M')

    return {
        'title': report_data.get('metadata', {}).get('title', '测评报告'),
        'word_count': core_data.get('wordCount', 0),
        'total_score': core_data.get('totalScore', 0),
        'full_mark': core_data.get('fullMark', 100),
        'dimension_scores': core_data.get('dimensionScores', []),
        'comprehensive_comment': core_data.get('comprehensiveComment', ''),
        'improvement_suggestions': core_data.get('improvementSuggestions', []),
        'submit_time': submit_time
    }


def generate_html_report(json_file_path: str, output_path: str = None) -> str:
    """生成HTML报告"""
    try:
        from jinja2 import Template
    except ImportError:
        print("请安装jinja2: pip install jinja2")
        sys.exit(1)

    # 解析数据
    data = parse_report_data(json_file_path)

    # 准备雷达图数据
    dimension_data = [
        {
            'name': dim['evaluationDimension'],
            'value': dim['dimensionScore'],
            'max': dim['dimensionFullMark']
        }
        for dim in data['dimension_scores']
    ]

    # 渲染模板
    template = Template(HTML_TEMPLATE)
    html_content = template.render(
        **data,
        dimension_data_json=json.dumps(dimension_data, ensure_ascii=False)
    )

    # 输出文件
    if output_path is None:
        base_name = Path(json_file_path).stem
        output_path = str(Path(json_file_path).parent / f"{base_name}_report.html")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"报告已生成: {output_path}")
    return output_path


def generate_pdf_report(html_path: str, pdf_path: str = None) -> str:
    """使用Playwright将HTML转为PDF"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("生成PDF需要安装playwright: pip install playwright && playwright install chromium")
        return None

    if pdf_path is None:
        pdf_path = html_path.replace('.html', '.pdf')

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f'file://{os.path.abspath(html_path)}')
        page.wait_for_timeout(1000)  # 等待图表渲染
        page.pdf(path=pdf_path, format='A4', print_background=True)
        browser.close()

    print(f"PDF已生成: {pdf_path}")
    return pdf_path


def main():
    if len(sys.argv) < 2:
        print("用法: python report_generator.py <json_file_path> [output_html_path]")
        print("示例: python report_generator.py result.json report.html")
        sys.exit(1)

    json_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.exists(json_file):
        print(f"文件不存在: {json_file}")
        sys.exit(1)

    html_path = generate_html_report(json_file, output_file)

    # 询问是否生成PDF
    try:
        response = input("是否生成PDF? (y/n): ").strip().lower()
        if response == 'y':
            generate_pdf_report(html_path)
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == '__main__':
    main()
