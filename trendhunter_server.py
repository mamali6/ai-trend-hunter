#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import http.server
import json
import os
import re
import sys
import time
import threading
import urllib.request
import urllib.parse

PORT = 8892

cache = {
    "trends": [],
    "last_update": 0,
    "lock": threading.Lock(),
    "stats": {}
}

FLAGSHIP_AI = [
    {
        "id": "flagship-claude-37",
        "source": "Anthropic",
        "source_icon": "🧠",
        "title": "Claude 3.7 Sonnet: First Hybrid Reasoning LLM",
        "summary": "First model with dynamic hybrid reasoning: instant responses or extended step-by-step thinking up to 128k tokens. Leads in coding benchmarks (SWE-bench 70.3%) and full agentic autonomy.",
        "stars": 9800,
        "upvotes": 1450,
        "url": "https://www.anthropic.com/news/claude-3-7-sonnet",
        "category": "models",
        "category_fa": "مدل پرچمدار",
        "badge": "🔥 داغ‌ترین مدل",
        "virality_score": 99,
        "tags": ["Reasoning", "Coding", "Anthropic", "SWE-bench"]
    },
    {
        "id": "flagship-deepseek-r1",
        "source": "DeepSeek",
        "source_icon": "🐋",
        "title": "DeepSeek-R1: Open-Weight Reasoning Breakthrough",
        "summary": "Fully open-weights reasoning model trained with pure reinforcement learning (RL) without supervised fine-tuning. Matches OpenAI o1 on math, coding, and logical tasks at 95% lower cost.",
        "stars": 74500,
        "upvotes": 3200,
        "url": "https://github.com/deepseek-ai/DeepSeek-R1",
        "category": "models",
        "category_fa": "مدل متن‌باز",
        "badge": "⚡ متن‌باز انقلابی",
        "virality_score": 98,
        "tags": ["OpenSource", "DeepSeek", "Reasoning", "RL"]
    },
    {
        "id": "flagship-browser-use",
        "source": "GitHub",
        "source_icon": "🌐",
        "title": "Browser Use: Make AI Agents Interact with Any Website",
        "summary": "Open-source Python library allowing LLM agents to interact with web browsers just like a human. Supports clicking, filling forms, extracting DOM, solving captchas, and multi-step tasks.",
        "stars": 34800,
        "upvotes": 890,
        "url": "https://github.com/browser-use/browser-use",
        "category": "agents",
        "category_fa": "ایجنت وب",
        "badge": "⭐ ۳۴K ستاره",
        "virality_score": 96,
        "tags": ["Agents", "Automation", "Browser", "Python"]
    },
    {
        "id": "flagship-qwen-coder",
        "source": "Alibaba Cloud",
        "source_icon": "💻",
        "title": "Qwen 2.5 Coder: The Best Open-Source Coding Model",
        "summary": "State-of-the-art open-weights coding model with 32B parameters. Competes directly with GPT-4o on code generation, debugging, refactoring, and multi-file project understanding.",
        "stars": 18200,
        "upvotes": 750,
        "url": "https://github.com/QwenLM/Qwen2.5-Coder",
        "category": "repos",
        "category_fa": "کدنویسی هوشمند",
        "badge": "🚀 برترین مدل کد",
        "virality_score": 95,
        "tags": ["Coding", "OpenWeights", "Qwen", "Python"]
    },
    {
        "id": "flagship-sora-gen",
        "source": "OpenAI / SOTA",
        "source_icon": "🎥",
        "title": "Next-Gen Diffusion Video Models & Cinematic Physics",
        "summary": "Breakthroughs in consistent multi-shot video generation with temporal coherence, camera trajectory control, and realistic physics simulation for creators.",
        "stars": 12400,
        "upvotes": 610,
        "url": "https://openai.com/sora",
        "category": "vision",
        "category_fa": "ویدیو و تصویر",
        "badge": "🎬 ویدیوی سینمایی",
        "virality_score": 94,
        "tags": ["Video", "Diffusion", "GenAI", "Creative"]
    }
]

def fetch_huggingface_papers():
    try:
        req = urllib.request.Request('https://huggingface.co/api/daily_papers', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for item in data[:15]:
                p = item.get('paper', {})
                pid = str(p.get('id', ''))
                upvotes = p.get('upvotes', 0)
                score = min(99, max(65, 70 + upvotes * 3))
                title = p.get('title', 'Unknown Paper')
                summary = p.get('summary', '') or 'Research paper on frontiers of machine learning.'
                summary = summary.replace('\n', ' ').strip()
                if len(summary) > 300:
                    summary = summary[:300] + '...'
                
                tags = ["Paper", "Research"]
                t_lower = (title + " " + summary).lower()
                if "reason" in t_lower: tags.append("Reasoning")
                if "agent" in t_lower: tags.append("Agents")
                if "vision" in t_lower or "image" in t_lower: tags.append("Vision")
                if "retrieval" in t_lower or "rag" in t_lower: tags.append("RAG")
                if "code" in t_lower: tags.append("Coding")

                results.append({
                    "id": f"hf-{pid}",
                    "source": "Hugging Face",
                    "source_icon": "🤗",
                    "title": title,
                    "summary": summary,
                    "upvotes": upvotes,
                    "stars": upvotes * 15,
                    "url": f"https://huggingface.co/papers/{pid}",
                    "published_at": p.get('publishedAt', ''),
                    "category": "papers",
                    "category_fa": "مقاله پژوهشی",
                    "badge": f"🤗 {upvotes} رای",
                    "virality_score": score,
                    "tags": tags[:4]
                })
            return results
    except Exception as e:
        print("HF error:", e)
        return []

def fetch_github_repos():
    try:
        req = urllib.request.Request('https://api.github.com/search/repositories?q=topic:llm+stars:>1000&sort=stars&order=desc&per_page=12', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for item in data.get('items', [])[:12]:
                stars = item.get('stargazers_count', 0)
                score = min(98, max(70, 75 + int(stars / 4000)))
                name = item.get('full_name', 'Repo')
                desc = item.get('description', '') or 'Open source AI project.'
                
                tags = ["GitHub", item.get('language', 'Code') or "Python"]
                d_lower = (name + " " + desc).lower()
                if "agent" in d_lower: tags.append("Agents")
                if "eval" in d_lower: tags.append("Benchmark")
                if "local" in d_lower: tags.append("Local AI")
                if "framework" in d_lower: tags.append("Framework")

                category = "agents" if "agent" in d_lower else "repos"
                category_fa = "ایجنت خودکار" if category == "agents" else "ریپازیتوری کد"

                results.append({
                    "id": f"gh-{item.get('id', '')}",
                    "source": "GitHub",
                    "source_icon": "🐙",
                    "title": name,
                    "summary": desc,
                    "stars": stars,
                    "forks": item.get('forks_count', 0),
                    "language": item.get('language', 'Python'),
                    "url": item.get('html_url', ''),
                    "category": category,
                    "category_fa": category_fa,
                    "badge": f"⭐ {stars:,}",
                    "virality_score": score,
                    "tags": tags[:4]
                })
            return results
    except Exception as e:
        print("GitHub error:", e)
        return []

def fetch_hackernews_ai():
    try:
        req = urllib.request.Request('https://hn.algolia.com/api/v1/search?query=AI+OR+LLM+OR+GPT&tags=story&hitsPerPage=10', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for item in data.get('hits', [])[:8]:
                points = item.get('points', 0)
                comments = item.get('num_comments', 0)
                score = min(97, max(68, 70 + int((points + comments * 2) / 15)))
                title = item.get('title', 'AI News')
                url = item.get('url') or f"https://news.ycombinator.com/item?id={item.get('objectID')}"

                results.append({
                    "id": f"hn-{item.get('objectID', '')}",
                    "source": "Hacker News",
                    "source_icon": "📰",
                    "title": title,
                    "summary": f"Discussion with {comments} comments and {points} upvotes across tech community.",
                    "stars": points,
                    "upvotes": points,
                    "url": url,
                    "category": "news",
                    "category_fa": "خبر و تحلیل",
                    "badge": f"🔥 {points} امتیاز",
                    "virality_score": score,
                    "tags": ["HackerNews", "TechNews", "Trends"]
                })
            return results
    except Exception as e:
        print("HN error:", e)
        return []

def refresh_all_trends():
    print("[TrendHunter] Refreshing AI trends...")
    hf = fetch_huggingface_papers()
    gh = fetch_github_repos()
    hn = fetch_hackernews_ai()

    all_items = FLAGSHIP_AI + gh + hf + hn
    all_items.sort(key=lambda x: x.get("virality_score", 0), reverse=True)

    stats = {
        "total_trends": len(all_items),
        "total_papers": len([x for x in all_items if x.get("category") == "papers"]),
        "total_repos": len([x for x in all_items if x.get("category") in ["repos", "agents"]]),
        "total_models": len([x for x in all_items if x.get("category") == "models"]),
        "avg_virality": round(sum(x.get("virality_score", 0) for x in all_items) / max(1, len(all_items)), 1),
        "last_updated": time.strftime("%H:%M:%S", time.localtime())
    }

    with cache["lock"]:
        cache["trends"] = all_items
        cache["stats"] = stats
        cache["last_update"] = time.time()
    print(f"[TrendHunter] Refreshed {len(all_items)} trends successfully!")

def background_worker():
    refresh_all_trends()
    while True:
        time.sleep(600)
        try:
            refresh_all_trends()
        except Exception as e:
            print("Worker refresh error:", e)

def generate_persian_thread(title, summary, tags=None, source="AI Trends", style="viral_hook", tweet_count=6):
    tags = tags or ["هوش_مصنوعی", "AI", "تکنولوژی"]
    clean_title = re.sub(r'https?://\S+', '', title).strip()
    
    t1 = (
        "🚨 بمب جدید دنیای هوش مصنوعی منفجر شد!\n\n"
        f"اگه فکر می‌کردید کار با مدل‌های قبلی اوج تکنولوژی بود، «{clean_title}» معادلات رو کاملاً تغییر داده!\n\n"
        "در این رشته‌توییت بررسی کردم چرا این دستاورد یک نقطه عطفه و چطور باید ازش استفاده کنید 👇\n\n"
        f"🧵 ۱/{tweet_count}"
    )

    t2 = (
        "قبل از این، بزرگ‌ترین چالش توسعه‌دهنده‌ها و کسب‌وکارها چی بود؟\n\n"
        "❌ هزینه‌های سنگین پردازش و مصرف توکن\n"
        "❌ دقت پایین در کارهای استدلالی پیچیده و توهم (Hallucination)\n"
        "❌ وابستگی شدید به APIهای بسته و غیرقابل شخصی‌سازی\n\n"
        "حالا ببینیم این ابزار چطور این گره رو باز کرده:\n\n"
        f"🧵 ۲/{tweet_count}"
    )

    t3 = (
        "⚡ نوآوری فنی چیه و چرا همه دارن راجع بهش حرف می‌زنن؟\n\n"
        f"خلاصه فنی: {summary[:240]}\n\n"
        "نکته شگفت‌انگیز اینه که این سیستم به جای رویکرد سنتی، از معماری هوشمند گام‌به‌گام و پایش لحظه‌ای عملکرد استفاده می‌کنه.\n\n"
        f"🧵 ۳/{tweet_count}"
    )

    t4 = (
        "📊 در بنچمارک‌ها و نتایج عملی چی دیدیم؟\n\n"
        "تست‌های مقایسه‌ای نشون میده که در حل تسک‌های چندمرحله‌ای، سرعت پاسخ‌دهی و حل باگ‌های برنامه‌نویسی، خروجی به شکل معناداری از مدل‌های نسل قبل جلوتره.\n\n"
        "یعنی کاری که قبلاً نیم‌ساعت وقت می‌گرفت، حالا در چند ثانیه با دقت بسیار بالا تحویل میشه.\n\n"
        f"🧵 ۴/{tweet_count}"
    )

    t5 = (
        "🛠️ چطور خودمون تستش کنیم و به کارش بگیریم؟\n\n"
        f"دسترسی به کد، مستندات و دموهای رسمی از طریق مخزن بازه:\n"
        f"🔗 منبع: {source}\n\n"
        "کافیه دپندینسی‌ها رو طبق راهنما نصب کنید یا دموی تحت وب رو تست بزنید تا پتانسیل واقعیش رو به چشم ببینید.\n\n"
        f"🧵 ۵/{tweet_count}"
    )

    tag_str = " ".join([f"#{t.replace(' ', '_').replace('-', '_')}" for t in tags[:4]])
    t6 = (
        "💡 جمع‌بندی و دیدگاه من:\n\n"
        "سرعت رشد هوش مصنوعی شوخی‌بردار نیست! کسایی که این ابزارها رو سریع‌تر وارد جریان کاری خودشون کنن، برنده بازار خواهند بود.\n\n"
        "🔁 اگه این ترد برات جذاب و مفید بود، حتماً ریتوییت کن و بوکمارکش کن تا گمش نکنی!\n"
        "نظر شما راجع به این ترند چیه؟\n\n"
        f"{tag_str}\n\n"
        f"🧵 {tweet_count}/{tweet_count}"
    )

    tweets = [t1, t2, t3, t4, t5, t6]

    telegram_post = (
        f"🔥 **تحلیل ترند داغ هوش مصنوعی | {clean_title}**\n\n"
        f"📌 **چرا همه دارن راجع به این صحبت می‌کنن؟**\n"
        f"{summary}\n\n"
        f"✨ **ویژگی‌های برجسته:**\n"
        f"• عملکرد جهشی در استدلال و کارهای پیچیده\n"
        f"• کاهش چشمگیر هزینه و زمان اجرای پروژه‌ها\n"
        f"• معماری مدرن و سازگار با توسعه‌دهندگان\n\n"
        f"🔗 **منبع و دسترسی:** {source}\n\n"
        f"{tag_str}\n"
        f"🆔 @Mohammad_AI"
    )

    linkedin_post = (
        f"🚀 تحول جدید در اکوسیستم هوش مصنوعی: {clean_title}\n\n"
        f"در دنیای سریع امروز، ابزارهایی که بتوانند بهره‌وری مهندسی و تصمیم‌گیری خودکار را افزایش دهند، مزیت رقابتی سازمان‌ها خواهند بود.\n\n"
        f"خلاصه این دستاورد:\n{summary}\n\n"
        f"سه پیامد استراتژیک این فناوری:\n"
        f"۱. دموکراتیزه شدن توسعه نرم‌افزار با ایجنت‌های هوشمند\n"
        f"۲. بهینه‌سازی هزینه‌های زیرساخت پردازشی\n"
        f"۳. ایجاد جریان‌های درآمدی جدید بر پایه هوش مصنوعی کاربردی\n\n"
        f"آیا سازمان یا تیم شما آماده پیاده‌سازی این ابزارها هست؟ مشتاق شنیدن تجربیات شما در بخش نظرات هستم.\n\n"
        f"{tag_str}"
    )

    key_takeaways = [
        "شکستن رکوردهای بنچمارک در تست‌های استدلال و کدنویسی",
        "پتانسیل بالا برای اتوماسیون وظایف زمان‌بر برنامه‌نویسی و تحلیل داده",
        "دسترسی عمومی و امکان تست در محیط‌های شخصی و شرکتی"
    ]

    return {
        "title": clean_title,
        "virality_score": 96,
        "tweets": tweets,
        "telegram_post": telegram_post,
        "linkedin_post": linkedin_post,
        "key_takeaways": key_takeaways,
        "hashtags": tags
    }

class TrendHandler(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path in ["/api/trends", "/trends"]:
            with cache["lock"]:
                trends = list(cache["trends"])
                stats = dict(cache["stats"])

            cat = query.get("category", ["all"])[0]
            if cat != "all":
                trends = [t for t in trends if t.get("category") == cat]

            payload = {
                "status": "ok",
                "stats": stats,
                "count": len(trends),
                "trends": trends
            }
            body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif path in ["/api/stats", "/stats"]:
            with cache["lock"]:
                stats = dict(cache["stats"])
            body = json.dumps(stats, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif path in ["/api/health", "/health", "/"]:
            body = json.dumps({"status": "ok", "service": "AI Trend Hunter Backend", "port": PORT}, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ["/api/generate", "/generate"]:
            content_len = int(self.headers.get('Content-Length', 0))
            raw_body = self.rfile.read(content_len).decode('utf-8')
            try:
                data = json.loads(raw_body)
            except Exception:
                data = {}

            trend_id = data.get("trend_id")
            custom_topic = data.get("custom_topic", "").strip()
            style = data.get("style", "viral_hook")

            title = "انقلاب جدید در هوش مصنوعی"
            summary = "پیشرفت‌های جدید در ایجنت‌های خودکار و مدل‌های استدلالی."
            tags = ["AI", "هوش_مصنوعی", "تکنولوژی", "نوآوری"]
            source = "AI Radar"

            if custom_topic:
                title = custom_topic
                summary = f"بررسی جامع و موشکافانه موضوع «{custom_topic}» و تاثیر آن بر آینده توسعه نرم‌افزار و ابزارهای هوشمند."
                tags = [custom_topic[:15].replace(" ", "_"), "هوش_مصنوعی", "فناوری"]
            elif trend_id:
                with cache["lock"]:
                    matched = [t for t in cache["trends"] if t.get("id") == trend_id]
                    if matched:
                        item = matched[0]
                        title = item.get("title", title)
                        summary = item.get("summary", summary)
                        tags = item.get("tags", tags)
                        source = item.get("source", source)

            thread_result = generate_persian_thread(title, summary, tags, source, style)
            body = json.dumps({"status": "ok", "data": thread_result}, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    t = threading.Thread(target=background_worker, daemon=True)
    t.start()
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), TrendHandler)
    print(f"AI Trend Hunter Backend listening on http://0.0.0.0:{PORT}")
    server.serve_forever()
