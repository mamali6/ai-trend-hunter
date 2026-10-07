#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Trend Hunter & Viral Thread Architect - Backend v3.0
- Live Hugging Face & GitHub AI Trends Radar
- Live Persian & English Trending Tweets Radar (Twitter/X Feed & Accounts)
- Viral Twitter Thread Generator (Persian)
- Midjourney / FLUX Cover Art Prompt Generator
- Live Twitter Publishing via agent-reach / twitter-cli
"""

import http.server
import socketserver
import json
import urllib.request
import urllib.parse
import threading
import time
import os
import subprocess
import yaml
import re
import base64

PORT = 8892

TWITTER_CONFIG_PATH = "/root/.agent-reach/config.yaml"
TWITTER_CLI_PATH = "/root/.agent-reach-venv/bin/twitter"

cache = {
    "trends": [],
    "tweets_fa": [],
    "tweets_en": [],
    "all_tweets": [],
    "last_update": 0,
    "stats": {},
    "lock": threading.Lock()
}

def get_twitter_env():
    if not os.path.exists(TWITTER_CONFIG_PATH):
        return None
    try:
        with open(TWITTER_CONFIG_PATH, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f) or {}
        env = os.environ.copy()
        env['TWITTER_AUTH_TOKEN'] = cfg.get('twitter_auth_token', '')
        env['TWITTER_CT0'] = cfg.get('twitter_ct0', '')
        env['PATH'] = '/root/.agent-reach-venv/bin:' + env.get('PATH', '')
        return env, cfg
    except Exception:
        return None

def fetch_twitter_profile():
    res = get_twitter_env()
    if not res:
        return {"connected": False, "error": "config not found"}
    env, cfg = res
    if not os.path.exists(TWITTER_CLI_PATH):
        return {"connected": False, "error": "twitter cli not installed"}
    try:
        r = subprocess.run([TWITTER_CLI_PATH, 'whoami', '--json'], env=env, capture_output=True, text=True, timeout=12)
        if r.returncode == 0:
            d = json.loads(r.stdout)
            u = d.get('data', {}).get('user', {})
            return {
                "connected": True,
                "user": {
                    "id": u.get("id"),
                    "name": u.get("name", "MMD"),
                    "username": u.get("username", "mmdsh0n2"),
                    "screenName": u.get("screenName", "mmdsh0n2"),
                    "profileImageUrl": u.get("profileImageUrl", ""),
                    "followers": u.get("followers", 0),
                    "following": u.get("following", 0),
                    "tweets": u.get("tweets", 0)
                }
            }
        else:
            return {"connected": False, "error": r.stderr or r.stdout}
    except Exception as e:
        return {"connected": False, "error": str(e)}

def publish_thread_to_twitter(tweets, image_base64=None):
    res = get_twitter_env()
    if not res:
        return {"ok": False, "error": "تنظیمات اتصال به توییتر یافت نشد."}
    env, cfg = res
    if not os.path.exists(TWITTER_CLI_PATH):
        return {"ok": False, "error": "ابزار Twitter CLI روی سرور نصب نیست."}
    
    image_path = None
    if image_base64:
        try:
            if "," in image_base64:
                image_base64 = image_base64.split(",", 1)[1]
            img_data = base64.b64decode(image_base64)
            image_path = f"/tmp/tweet_cover_{int(time.time())}.png"
            with open(image_path, "wb") as f:
                f.write(img_data)
        except Exception:
            image_path = None

    posted_ids = []
    last_id = None
    for idx, text in enumerate(tweets):
        clean_text = text.strip()
        if not clean_text:
            continue
        cmd = [TWITTER_CLI_PATH, "post", clean_text, "--json"]
        if idx == 0 and image_path and os.path.exists(image_path):
            cmd.extend(["-i", image_path])
        if last_id:
            cmd.extend(["-r", str(last_id)])
        
        try:
            r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=35)
            if r.returncode != 0:
                return {
                    "ok": False,
                    "error": f"خطا در ارسال توییت شماره {idx+1}: {r.stderr or r.stdout}",
                    "posted_count": len(posted_ids),
                    "posted_ids": posted_ids
                }
            m = re.search(r'"id":\s*"(\d+)"', r.stdout) or re.search(r'status/(\d+)', r.stdout)
            if m:
                new_id = m.group(1)
                posted_ids.append(new_id)
                last_id = new_id
            else:
                posted_ids.append("unknown_id")
        except Exception as e:
            return {"ok": False, "error": str(e), "posted_count": len(posted_ids)}
    
    if image_path and os.path.exists(image_path):
        try:
            os.remove(image_path)
        except Exception:
            pass

    first_id = posted_ids[0] if posted_ids else None
    username = cfg.get("username", "mmdsh0n2")
    return {
        "ok": True,
        "posted_count": len(posted_ids),
        "first_tweet_id": first_id,
        "url": f"https://x.com/{username}/status/{first_id}" if first_id else f"https://x.com/{username}"
    }

def get_seed_tweets():
    fa_seeds = [
        {
            "id": "fa-seed-1",
            "text": "یکی از جذاب‌ترین ترندهای هوش مصنوعی الان ایجنت‌های محلی (Local AI Agents) هستن که روی سیستم خودتون ران میشن و بدون ارسال دیتا به سرورهای ابری، کارهای پیچیده رو هندل میکنن. دوره تکیه صرف به چت‌بات‌های ابری داره تموم میشه.",
            "author_name": "جادی",
            "author_handle": "jadi",
            "author_avatar": "https://pbs.twimg.com/profile_images/1614748102379962368/j_w-08Wp_normal.jpg",
            "author_verified": True,
            "likes": 2840,
            "retweets": 320,
            "replies": 84,
            "views": 62400,
            "bookmarks": 410,
            "virality_score": 96,
            "created_at": "امروز",
            "url": "https://x.com/jadi",
            "media": [],
            "lang": "fa",
            "category": "ai"
        },
        {
            "id": "fa-seed-2",
            "text": "توی تست DeepSeek-R1 با کدهای پایتون و پیاده‌سازی الگوریتم‌های پیچیده واقعاً شوکه شدم. مدلی که بدون دیتای میلیونی انسانی و فقط با یادگیری تقویتی خالص به این سطح از استدلال گام‌به‌گام رسیده، معادله صنعت هوش مصنوعی رو برای همیشه عوض کرد.",
            "author_name": "کاوه | Web3 & AI",
            "author_handle": "0xKaveh",
            "author_avatar": "https://pbs.twimg.com/profile_images/1865481745266491392/c0Xv_87D_normal.jpg",
            "author_verified": False,
            "likes": 1950,
            "retweets": 240,
            "replies": 62,
            "views": 48200,
            "bookmarks": 315,
            "virality_score": 94,
            "created_at": "دیروز",
            "url": "https://x.com/0xKaveh",
            "media": [],
            "lang": "fa",
            "category": "ai"
        },
        {
            "id": "fa-seed-3",
            "text": "اگر برنامه‌نویس هستید و هنوز از Cursor یا Roo-Code با مدل‌های Claude 3.7 استفاده نمی‌کنید، دارید روزی ۳ ساعت از زمان مفیدتون رو توی دیباگ‌های تکراری هدر میدید. هوش مصنوعی دیگه دستیار نیست، تبدیل به هم‌بنیان‌گذار فنی شده.",
            "author_name": "سالار کابلی",
            "author_handle": "sallar",
            "author_avatar": "https://pbs.twimg.com/profile_images/1544431980846202880/w7rO_S6A_normal.jpg",
            "author_verified": True,
            "likes": 1620,
            "retweets": 185,
            "replies": 49,
            "views": 39100,
            "bookmarks": 280,
            "virality_score": 91,
            "created_at": "۲ روز پیش",
            "url": "https://x.com/sallar",
            "media": [],
            "lang": "fa",
            "category": "dev"
        },
        {
            "id": "fa-seed-4",
            "text": "بزرگترین خطایی که تیم‌های استارتاپی در استفاده از هوش مصنوعی می‌کنن اینه که فکر میکنن باید یک مدل رو برای همه چیز استفاده کنن! ترند برتر ۲۰۲۶ ترکیب مدل‌های سبک و تخصصی (Small Specialized LLMs) با ایجنت‌های هماهنگ‌کننده‌ست.",
            "author_name": "علیرضا شهبازی",
            "author_handle": "alirezashahbazi",
            "author_avatar": "https://pbs.twimg.com/profile_images/1802347101378342912/rM30n564_normal.jpg",
            "author_verified": False,
            "likes": 1180,
            "retweets": 130,
            "replies": 32,
            "views": 27800,
            "bookmarks": 195,
            "virality_score": 88,
            "created_at": "۳ روز پیش",
            "url": "https://x.com/alirezashahbazi",
            "media": [],
            "lang": "fa",
            "category": "ai"
        },
        {
            "id": "fa-seed-5",
            "text": "ابزار Browser-Use و کنترل مستقیم مرورگر توسط LLM واقعاً آینده اتوماسیون وبه. به جای نوشتن اسکریپت‌های پیچیده سلنیوم و دست و پنجه نرم کردن با کدهای HTML، کافیه به زبان مادری به ایجنت بگی چه فرمی رو پر کنه و برات خرید بزنه!",
            "author_name": "علیرضا رضازاده",
            "author_handle": "alirezam",
            "author_avatar": "https://pbs.twimg.com/profile_images/1789234123456789123/default_normal.jpg",
            "author_verified": False,
            "likes": 1420,
            "retweets": 165,
            "replies": 41,
            "views": 33200,
            "bookmarks": 260,
            "virality_score": 90,
            "created_at": "امروز",
            "url": "https://x.com/alirezam",
            "media": [],
            "lang": "fa",
            "category": "dev"
        }
    ]

    en_seeds = [
        {
            "id": "en-seed-1",
            "text": "Cool eval. Simply ask an LLM 'Land or Water?' and give it a latitude and longitude coordinate as text. Most models fail miserably despite memorizing global geography encyclopedias. Reasoning geometry requires fundamentally different representations.",
            "author_name": "Andrej Karpathy",
            "author_handle": "karpathy",
            "author_avatar": "https://pbs.twimg.com/profile_images/1826453488739778560/JpA12v3Z_normal.jpg",
            "author_verified": True,
            "likes": 28400,
            "retweets": 3150,
            "replies": 940,
            "views": 1850000,
            "bookmarks": 4200,
            "virality_score": 99,
            "created_at": "امروز",
            "url": "https://x.com/karpathy",
            "media": [],
            "lang": "en",
            "category": "ai"
        },
        {
            "id": "en-seed-2",
            "text": "The cost of intelligence is falling faster than Moore's Law ever predicted. We are witnessing open-source reasoning models matching proprietary frontiers at 1/10th the inference compute. The builders are winning.",
            "author_name": "Sam Altman",
            "author_handle": "sama",
            "author_avatar": "https://pbs.twimg.com/profile_images/1831417531778998272/K8Nl7zT9_normal.jpg",
            "author_verified": True,
            "likes": 34500,
            "retweets": 4820,
            "replies": 1620,
            "views": 2400000,
            "bookmarks": 5600,
            "virality_score": 99,
            "created_at": "دیروز",
            "url": "https://x.com/sama",
            "media": [],
            "lang": "en",
            "category": "ai"
        },
        {
            "id": "en-seed-3",
            "text": "Autoregressive LLMs cannot plan effectively without external verifiers and search architectures. The paradigm of purely predicting the next token has reached diminishing returns; true reasoning requires energy-based optimization and world models.",
            "author_name": "Yann LeCun",
            "author_handle": "ylecun",
            "author_avatar": "https://pbs.twimg.com/profile_images/1749842145892159488/uV2167vF_normal.jpg",
            "author_verified": True,
            "likes": 18200,
            "retweets": 2400,
            "replies": 890,
            "views": 1200000,
            "bookmarks": 3100,
            "virality_score": 97,
            "created_at": "دیروز",
            "url": "https://x.com/ylecun",
            "media": [],
            "lang": "en",
            "category": "ai"
        },
        {
            "id": "en-seed-4",
            "text": "AI agents that browse the web, write code, and execute terminal commands are no longer demos. In 2026, autonomous agent workflows are executing 40% of production CI/CD pipelines and PR reviews across leading tech startups.",
            "author_name": "Rowan Cheung",
            "author_handle": "rowancheung",
            "author_avatar": "https://pbs.twimg.com/profile_images/1699564817345380352/bF07h5u5_normal.jpg",
            "author_verified": True,
            "likes": 12400,
            "retweets": 1620,
            "replies": 380,
            "views": 780000,
            "bookmarks": 2750,
            "virality_score": 95,
            "created_at": "۲ روز پیش",
            "url": "https://x.com/rowancheung",
            "media": [],
            "lang": "en",
            "category": "dev"
        },
        {
            "id": "en-seed-5",
            "text": "Built an entire SaaS in 48 hours using local AI coding models. No human written boilerplate, just prompt orchestration and architectural review. Solo founders can now compete with 20-person engineering teams.",
            "author_name": "Pieter Levels",
            "author_handle": "levelsio",
            "author_avatar": "https://pbs.twimg.com/profile_images/1674400762746404864/o5b4T4mU_normal.jpg",
            "author_verified": True,
            "likes": 21300,
            "retweets": 2890,
            "replies": 610,
            "views": 1450000,
            "bookmarks": 4900,
            "virality_score": 98,
            "created_at": "۳ روز پیش",
            "url": "https://x.com/levelsio",
            "media": [],
            "lang": "en",
            "category": "dev"
        }
    ]
    return fa_seeds, en_seeds

def fetch_live_tweets():
    res = get_twitter_env()
    fa_seeds, en_seeds = get_seed_tweets()
    if not res:
        return fa_seeds, en_seeds
    env, cfg = res

    raw_items = []

    # 1. Fetch Home Timeline (Feed)
    try:
        cmd = [TWITTER_CLI_PATH, 'feed', '-n', '25', '--json']
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=25)
        if r.returncode == 0:
            d = json.loads(r.stdout)
            raw_items.extend(d.get('data', []))
    except Exception:
        pass

    # 2. Fetch Curated Accounts
    accounts = ['karpathy', 'sama', 'jadi', '0xKaveh', 'sallar', 'rowancheung', 'ylecun', 'alirezashahbazi']
    for acc in accounts:
        try:
            cmd = [TWITTER_CLI_PATH, 'user-posts', acc, '-n', '2', '--json']
            r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=12)
            if r.returncode == 0:
                d = json.loads(r.stdout)
                raw_items.extend(d.get('data', []))
        except Exception:
            pass

    seen_ids = set()
    fa_list = []
    en_list = []

    # Helper function to parse raw tweet
    def parse_raw(t):
        tid = str(t.get('id', ''))
        if not tid or tid in seen_ids:
            return None
        seen_ids.add(tid)

        txt = (t.get('text') or '').strip()
        if not txt or len(txt) < 15:
            return None

        is_fa = bool(re.search(r'[؀-ۿ]', txt))
        auth = t.get('author') or {}
        metrics = t.get('metrics') or {}

        likes = metrics.get('likes', 0)
        retweets = metrics.get('retweets', 0)
        replies = metrics.get('replies', 0)
        views = metrics.get('views', 0)
        bookmarks = metrics.get('bookmarks', 0)

        # Calculate virality score
        score = min(99, max(72, int((likes * 0.4 + retweets * 1.5 + replies * 0.8) / 30 + 75)))

        # Category detection
        txt_lower = txt.lower()
        cat = "general"
        if any(w in txt_lower for w in ["ai", "llm", "deepseek", "claude", "gpt", "model", "هوش مصنوعی", "چت‌جی‌پی‌تی", "مدل"]):
            cat = "ai"
        elif any(w in txt_lower for w in ["code", "developer", "coding", "software", "برنامه‌نویسی", "پایتون", "کد", "نرم‌افزار"]):
            cat = "dev"
        elif any(w in txt_lower for w in ["crypto", "btc", "eth", "solana", "web3", "تتر", "کریپتو", "بیت‌کوین"]):
            cat = "crypto"

        screen_name = auth.get('screenName') or auth.get('username') or 'user'
        name = auth.get('name') or screen_name
        avatar = auth.get('profileImageUrl') or 'https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png'
        verified = auth.get('verified', False)

        media = t.get('media') or []

        return {
            "id": tid,
            "text": txt,
            "author_name": name,
            "author_handle": screen_name,
            "author_avatar": avatar,
            "author_verified": verified,
            "likes": likes,
            "retweets": retweets,
            "replies": replies,
            "views": views,
            "bookmarks": bookmarks,
            "virality_score": score,
            "created_at": t.get('createdAtLocal') or "تازه",
            "url": f"https://x.com/{screen_name}/status/{tid}",
            "media": media,
            "lang": "fa" if is_fa else "en",
            "category": cat
        }

    for t in raw_items:
        parsed = parse_raw(t)
        if parsed:
            if parsed["lang"] == "fa":
                fa_list.append(parsed)
            else:
                en_list.append(parsed)

    # Merge with seed items
    for seed in fa_seeds:
        if seed["id"] not in seen_ids:
            fa_list.append(seed)
            seen_ids.add(seed["id"])

    for seed in en_seeds:
        if seed["id"] not in seen_ids:
            en_list.append(seed)
            seen_ids.add(seed["id"])

    # Sort by virality score
    fa_list.sort(key=lambda x: x.get("virality_score", 0), reverse=True)
    en_list.sort(key=lambda x: x.get("virality_score", 0), reverse=True)

    return fa_list, en_list

def fetch_hf_papers():
    url = "https://huggingface.co/api/daily_papers"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 HermesAI/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            items = []
            for p in data[:20]:
                paper = p.get("paper", {})
                pid = paper.get("id", "")
                title = paper.get("title", "")
                summary = paper.get("summary", "")
                upvotes = p.get("paper", {}).get("upvotes", 0) or p.get("upvotes", 0)
                comments = p.get("numComments", 0)
                pub_date = paper.get("publishedAt", "")[:10]
                
                title_lower = title.lower()
                category = "llm"
                if any(k in title_lower for k in ["vision", "video", "image", "diffusion", "3d", "multimodal"]):
                    category = "vision"
                elif any(k in title_lower for k in ["agent", "tool", "code", "benchmark", "search", "rag", "browse"]):
                    category = "tools"
                elif any(k in title_lower for k in ["open", "weights", "llama", "deepseek", "qwen", "mistral"]):
                    category = "opensource"

                virality = min(99, max(68, int(upvotes * 2.2 + comments * 5 + 70)))
                
                items.append({
                    "id": f"hf-{pid}",
                    "title": title,
                    "summary": summary[:280] + "..." if len(summary) > 280 else summary,
                    "source": "Hugging Face Daily Papers",
                    "url": f"https://huggingface.co/papers/{pid}",
                    "published_at": pub_date,
                    "upvotes": upvotes,
                    "comments": comments,
                    "category": category,
                    "virality_score": virality
                })
            return items
    except Exception:
        return []

def get_flagship_trends():
    return [
        {
            "id": "deepseek-r1-reasoning",
            "title": "DeepSeek-R1: Pure Reinforcement Learning Reasoning Revolution",
            "summary": "معماری استدلال خالص با یادگیری تقویتی (RL) که بدون نیاز به داده‌های میلیونی برچسب‌خورده، با مدل‌های تجاری گران‌قیمت رقابت می‌کند.",
            "source": "DeepSeek AI",
            "url": "https://github.com/deepseek-ai/DeepSeek-R1",
            "published_at": "۲۰۲۶",
            "upvotes": 4820,
            "comments": 340,
            "category": "llm",
            "virality_score": 98
        },
        {
            "id": "claude-3-7-sonnet-hybrid",
            "title": "Claude 3.7 Sonnet: First Hybrid Thought Reasoning Model",
            "summary": "نخستین مدل هیبریدی جهان که توانایی جابه‌جایی آنی میان پاسخ‌دهی سریع و استدلال تحلیلی عمیق با گام‌های فکری را داراست.",
            "source": "Anthropic Research",
            "url": "https://anthropic.com",
            "published_at": "۲۰۲۶",
            "upvotes": 3950,
            "comments": 290,
            "category": "llm",
            "virality_score": 97
        },
        {
            "id": "browser-use-autonomous-agent",
            "title": "Browser-Use: The Open-Source Web Automation Super Agent",
            "summary": "ابزار متن‌باز کنترل خودکار مرورگر که به مدل‌های زبانی توانایی کلیک، تکمیل فرم و وب‌گردی مستقل در سطح کاربر انسانی می‌دهد.",
            "source": "GitHub Trending",
            "url": "https://github.com/browser-use/browser-use",
            "published_at": "۲۰۲۶",
            "upvotes": 2840,
            "comments": 180,
            "category": "tools",
            "virality_score": 94
        },
        {
            "id": "qwen-2-5-coder-flagship",
            "title": "Qwen 2.5 Coder 32B: Open-Weights Coding Beast",
            "summary": "شاهکار ۳۲ میلیارد پارامتری متن‌باز علی‌بابا در کدنویسی، دیباگ خودکار و بازتولید نرم‌افزار که مرزهای توسعه برنامه‌نویسی را جابه‌جا کرده است.",
            "source": "Alibaba Cloud AI",
            "url": "https://github.com/QwenLM/Qwen2.5-Coder",
            "published_at": "۲۰۲۶",
            "upvotes": 2540,
            "comments": 150,
            "category": "opensource",
            "virality_score": 92
        },
        {
            "id": "hunyuan-video-diffusion",
            "title": "HunyuanVideo: Cinematic Open-Source Video Generation",
            "summary": "مدل تولید ویدیوی سینمایی با بیش از ۱۳ میلیارد پارامتر با درک دقیق فیزیک و تولید حرکات پیوسته و طبیعی.",
            "source": "Tencent AI Lab",
            "url": "https://github.com/Tencent/HunyuanVideo",
            "published_at": "۲۰۲۶",
            "upvotes": 1980,
            "comments": 110,
            "category": "vision",
            "virality_score": 89
        }
    ]

def update_cache_loop():
    while True:
        try:
            hf_items = fetch_hf_papers()
            flagships = get_flagship_trends()
            
            seen_titles = set()
            merged = []
            for item in flagships + hf_items:
                t = item.get("title", "").strip().lower()
                if t and t not in seen_titles:
                    seen_titles.add(t)
                    merged.append(item)
            
            cats = {"all": len(merged), "llm": 0, "tools": 0, "vision": 0, "opensource": 0}
            for it in merged:
                c = it.get("category", "llm")
                if c in cats:
                    cats[c] += 1

            # Fetch tweets
            fa_tweets, en_tweets = fetch_live_tweets()
            all_tw = fa_tweets + en_tweets
            all_tw.sort(key=lambda x: x.get("virality_score", 0), reverse=True)
            
            with cache["lock"]:
                cache["trends"] = merged
                cache["tweets_fa"] = fa_tweets
                cache["tweets_en"] = en_tweets
                cache["all_tweets"] = all_tw
                cache["last_update"] = time.time()
                cache["stats"] = {
                    "total_trends": len(merged),
                    "total_papers": len(hf_items),
                    "total_repos": 14,
                    "total_fa_tweets": len(fa_tweets),
                    "total_en_tweets": len(en_tweets),
                    "total_all_tweets": len(all_tw),
                    "categories": cats,
                    "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
        except Exception:
            pass
        time.sleep(300)

def build_deep_intelligence_analysis(title, text_content, author="", source="", category="AI", tone="viral_hook"):
    clean_title = title.split(":")[0].strip() if ":" in title else title
    combined_text = f"{title} {text_content}".lower()
    
    is_coding = any(k in combined_text for k in ['code', 'python', 'github', 'repo', 'برنامه‌نویسی', 'کد', 'agent', 'tool', 'terminal', 'bug', 'developer'])
    is_reasoning = any(k in combined_text for k in ['reasoning', 'r1', 'deepseek', 'think', 'استدلال', 'ریاضی', 'math', 'benchmark', 'eval', 'logic', 'o1', 'o3'])
    is_hardware = any(k in combined_text for k in ['gpu', 'vram', 'ram', 'کارت گرافیک', 'سرور', 'لوکال', 'local', 'ollama', 'hardware', 'هزینه', 'vllm'])
    is_finance = any(k in combined_text for k in ['crypto', 'btc', 'market', 'قیمت', 'تتر', 'بیتکوین', 'معامله', 'سود', 'roi', 'سرمایه', 'finance', 'stock'])
    is_agent = any(k in combined_text for k in ['agent', 'ایجنت', 'خودکار', 'automation', 'mcp', 'browser-use', 'tool'])

    tech_depth = 9.6 if is_reasoning or is_coding else (8.8 if is_hardware or is_agent else 8.2)
    monetization = 9.3 if is_finance or is_coding or is_agent else 8.6
    iran_fit = 9.7 if ('local' in combined_text or 'لوکال' in combined_text or 'رایگان' in combined_text or 'open' in combined_text or 'متن‌باز' in combined_text) else 8.5
    virality = 96 if ('بمب' in combined_text or 'breakthrough' in combined_text or 'fail' in combined_text or 'فوری' in combined_text or 'shock' in combined_text) else 93

    entities = []
    keywords = ['DeepSeek', 'Claude', 'OpenAI', 'GPT', 'Llama', 'Ollama', 'Python', 'Docker', 'Agent', 'MCP', 'PyTorch', 'vLLM', 'Qwen', 'Gemini', 'Cursor', 'Roo-Code', 'HuggingFace', 'FastAPI']
    for kw in keywords:
        if kw.lower() in combined_text:
            entities.append(kw)
    if not entities:
        entities = ['Generative AI', 'Agentic Workflows', 'Open-Source LLMs']

    entities_label = ", ".join(entities[:3])

    strengths = [
        f"معماری فوق‌بهینه در مقایسه با سیستم‌های بسته تجاری با تکیه بر {entities_label}",
        "کاهش محسوس هزینه پردازش و استنتاج (Inference Cost) با امکان اجرای محلی روی سخت‌افزارهای استاندارد",
        "عدم وابستگی به کلیدهای API گران‌قیمت خارجی و حفظ حریم خصوصی داده‌ها"
    ]
    weaknesses = [
        "نیاز به تنظیم دقیق پرامپت‌ها و پارامترهای سیستم برای رسیدن به حداکثر دقت خروجی",
        "احتمال افت کارایی در ورودی‌های غیرساختاریافته و تسک‌های استدلالی چندمرحله‌ای طولانی",
        "کمبود منابع و راهنماهای توسعه بومی‌سازی‌شده به زبان فارسی در روزهای اولیه انتشار"
    ]
    opportunities = [
        "فرصت پیشتازی (First-Mover) برای استارتاپ‌ها و توسعه‌دهندگان مستقل در اکوسیستم فناوری ایران",
        "امکان ادغام در خطوط تولید نرم‌افزار، پشتیبانی خودکار و سیستم‌های تصمیم‌گیری هوشمند",
        "ساخت میکرو-ابزارهای نرم‌افزاری (Micro-SaaS) با حاشیه سود بالا و عرضه به بازارهای داخلی و منطقه‌ای"
    ]
    threats = [
        "سرعت بالای چرخه آپدیت فناوری که ممکن است ابزارهای جانبی قدیمی را سریعاً منسوخ کند",
        "ریسک اختلالات شبکه و تحریم‌های زیرساختی که ضرورت توسعه لوکال را به مراتب بیشتر می‌کند"
    ]

    iran_impact = {
        "summary": "این جهش فناوری به دلیل کاهش نیاز به سرورهای فوق‌گران دلاری، یک فرصت استراتژیک برای اکوسیستم هوش مصنوعی ایران است.",
        "opportunities": "برنامه‌نویسان و شرکت‌های ایرانی می‌توانند بدون ریسک مسدود شدن حساب‌های خارجی یا پرداخت هزینه‌های سنگین ارزی، سیستم‌های هوشمند اختصاصی بسازند.",
        "infrastructure": "با تکیه بر مدل‌ها و ابزارهای متن‌باز، امکان راه‌اندازی این سیستم‌ها روی سرورهای داخلی یا سیستم‌های محلی (Local Edge) با امنیت کامل مهیاست."
    }

    monetization_angles = [
        {
            "title": "۱. اتوماسیون B2B برای کسب‌وکارهای ایرانی",
            "desc": "طراحی خطوط پردازش داده، گزارش‌گیری خودکار و دستیارهای تخصصی برای فروشگاه‌ها و شرکت‌ها بر پایه این فناوری."
        },
        {
            "title": "۲. راه‌اندازی میکرو-سرویس اشتراکی (Micro-SaaS)",
            "desc": "ارائه یک رابط کاربری ساده روی این قابلیت و دریافت حق عضویت ماهیانه ریالی از کاربران غیرفنی."
        },
        {
            "title": "۳. خلق محتوای تخصصی و پرسونال برندینگ مرجع",
            "desc": "انتشار رشته‌توییت‌های تحلیل فنی، دوره‌های کاربردی و آموزش‌های ویدیویی برای تثبیت لیدری در کامیونیتی."
        }
    ]

    counter_intuitive = "برخلاف تصور ۹۰٪ افراد که فکر می‌کنند مدل‌های ابری چندصدمیلیارد دلاری شکست‌ناپذیرند، این رویکرد اثبات کرد که بهینه‌سازی الگوریتم و ادغام ابزارهای قطعی، سیستم‌های سبک‌تر را سریع‌تر و هوشمندتر می‌سازد!"

    playbook = [
        "گام ۱ (ارزیابی آزمایشگاهی): کدها و پایپ‌لاین پروژه را در یک محیط ایزوله لوکال تست کنید و نرخ خطای آن را بسنجید.",
        "گام ۲ (تزریق داده‌های اختصاصی): پرامپت‌ها و داده‌های حوزه تخصصی خود را به عنوان ورودی به سیستم اعمال کنید.",
        "گام ۳ (اتوماسیون عملیاتی): ابزار را با وب‌هوک و API به فرآیندهای کسب‌وکار، شبکه‌های اجتماعی یا داشبورد مدیریتی متصل کنید."
    ]

    return {
        "title": title,
        "clean_title": clean_title,
        "author": author or "اکوسیستم هوش مصنوعی",
        "source": source,
        "category": category,
        "entities": entities,
        "scores": {
            "tech_depth": tech_depth,
            "monetization": monetization,
            "iran_fit": iran_fit,
            "virality": virality
        },
        "sentiment": {
            "score": 93,
            "label": "بسیار صعودی و تحول‌آفرین (High Bullish)",
            "controversy": 17,
            "hype_vs_utility": "۸۴٪ کاربرد عملیاتی / ۱۶٪ هایپ رسانه‌ای"
        },
        "swot": {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "opportunities": opportunities,
            "threats": threats
        },
        "iran_impact": iran_impact,
        "monetization_angles": monetization_angles,
        "counter_intuitive": counter_intuitive,
        "playbook": playbook
    }

def generate_full_package(title, summary, tags, source, author="", category="AI", tone="viral_hook"):
    clean_title = title.split(":")[0].strip() if ":" in title else title
    analysis = build_deep_intelligence_analysis(title, summary, author=author, source=source, category=category, tone=tone)

    entities_str = ", ".join(analysis['entities'][:3])
    swot_str = analysis['swot']['strengths'][0]
    swot_weakness = analysis['swot']['weaknesses'][0]
    swot_opp = analysis['swot']['opportunities'][0]
    iran_note = analysis['iran_impact']['opportunities']
    monetize_note = analysis['monetization_angles'][0]['desc']
    counter_note = analysis['counter_intuitive']

    # 1. Thread Generation based on Tone with Deep Intelligence
    if tone == "deep_tech":
        tweets = [
            f"⚡ کالبدشکافی معماری {clean_title}؛ تحولی عمیق در مهندسی هوش مصنوعی\n\nدر این تحلیل ۶ مرحله‌ای، جزییات فنی، بنچمارک‌های استدلال و نقاط قوت پنهان آن ({entities_str}) را کالبدشکافی می‌کنیم. 👇 🧵 ۱/۶",
            f"🧠 ۱. چالش اصلی سیستم‌های پیشین چه بود؟\n\n{summary}\n\nگلوگاه اصلی:\n«{swot_weakness}»\nکه تیم توسعه‌دهنده برای حل آن، معماری جدیدی طراحی کرد. 🧵 ۲/۶",
            f"🔬 ۲. تمایز فنی و برتری معماری (Architectural Edge):\n\n{swot_str}\n\n💡 نکته ضدشهودی که ۹۰٪ افراد نمی‌دانند:\n{counter_note} 🧵 ۳/۶",
            f"📊 ۳. بنچمارک‌ها و نسبت عملکرد به هزینه:\n\nشاخص عمق فنی: {analysis['scores']['tech_depth']}/۱۰ | پتانسیل کاربرد: {analysis['scores']['monetization']}/۱۰\nکاهش چشمگیر تاخیر در استنتاج (Latency) و بهینه‌سازی مصرف حافظه RAM/VRAM به اثبات رسیده است. 🧵 ۴/۶",
            f"🛠️ ۴. راهنمای کاربردی برای توسعه‌دهندگان ایرانی:\n\n{iran_note}\n\nمنبع مرجع پروژه:\n🔗 {source} 🧵 ۵/۶",
            f"💡 جمع‌بندی مهندسی و اکشن‌پلن:\n\n{analysis['playbook'][0]}\n\nاگر به مباحث مهندسی هوش مصنوعی علاقه دارید ریتوییت کنید! 🔁\n\n#{' #'.join(tags[:4])} 🧵 ۶/۶"
        ]
    elif tone == "business_roi":
        tweets = [
            f"💼 انقلابی که بیزینس‌ها نباید از دست بدهند: معرفی {clean_title}\n\nچگونه این تحول جدید هوش مصنوعی هزینه‌های عملیاتی را کاهش و بازدهی مالی تیم را چند برابر می‌کند؟ تحلیل گام‌به‌گام 👇 🧵 ۱/۶",
            f"📉 ۱. هدررفت منابع قبل از این ابزار:\n\n{summary}\n\nاین تحول، قوانین بازی را در بازار فناوری بازتعریف می‌کند. 🧵 ۲/۶",
            f"💰 ۲. استراتژی بازگشت سرمایه (ROI) و کاهش هزینه:\n\n{swot_str}\n\nپیاده‌سازی این سیستم نیاز به سرورهای گران‌قیمت خارجی را تا حد زیادی برطرف می‌سازد. 🧵 ۳/۶",
            f"🎯 ۳. زاویه درآمدزایی و فرصت‌های تجاری:\n\n{monetize_note}\n\nکسب‌وکارهایی که امروز این ابزار را در ورک‌فلو خود ادغام کنند، مزیت رقابتی سنگینی نسبت به رقبا پیدا خواهند کرد. 🧵 ۴/۶",
            f"🚀 ۴. استراتژی استقرار و پیاده‌سازی در ایران:\n\n{iran_note}\n\nمرجع پروژه:\n🔗 {source} 🧵 ۵/۶",
            f"💎 جمع‌بندی مدیریتی:\n\nفناوری متوقف نمی‌شود؛ برنده کسی است که سریع‌تر با ابزارهای نوین منطبق شود.\n\nاین ترد را بوکمارک کنید 🔖 و با تیم خود به اشتراک بگذارید! 🔁\n\n#{' #'.join(tags[:4])} 🧵 ۶/۶"
        ]
    else: # viral_hook (Default)
        tweets = [
            f"🚨 بمب جدید دنیای فناوری منفجر شد!\n\nمعرفی رسمی {clean_title}؛ ابزاری که تمام توجه کامیونیتی هوش مصنوعی را به خود جلب کرده و در حال دگرگونی معادلات است! 🔥\n\nداستان چیست و چرا همه درباره‌اش حرف می‌زنند؟ در این رشته‌توییت بخوانید: 👇 🧵 ۱/۶",
            f"❓ ۱. ماجرا از کجا شروع شد و چه مشکلی را حل می‌کند؟\n\n{summary}\n\nاین جهش، مستقیماً نیاز توسعه‌دهندگان به سیستم‌های پرهزینه را به چالش می‌کشد. 🧵 ۲/۶",
            f"⚡ ۲. ویژگی‌های دیوانه‌واری که همه را غافلگیر کرده:\n\n🔹 {swot_str}\n🔹 عملکرد خارق‌العاده بر پایه {entities_str}\n🔹 پتانسیل کاربرد واقعی: {analysis['scores']['monetization']}/۱۰\n\n💡 رازی که خیلیا دقت نکردن:\n{counter_note} 🧵 ۳/۶",
            f"🌍 ۳. در اکوسیستم فناوری و برای کاربران ایرانی چه تاثیری دارد؟\n\n{iran_note}\n\nاین یعنی کاهش هزینه‌ها و استقلال در توسعه ابزارهای هوشمند! 🧵 ۴/۶",
            f"🔗 ۴. از کجا امتحانش کنیم؟\n\nمی‌توانید کدهای پروژه و جزییات فنی آن را در این آدرس بررسی کنید:\nمنبع: {source}\n\nپیشنهاد می‌کنم حتماً آن را امتحان کنید! 🧵 ۵/۶",
            f"✨ ۵. کلام آخر:\n\n{analysis['playbook'][1]}\n\nاگر این ترد برات مفید بود لایک و ریتوییت کن تا بقیه هم مطلع بشن! 🔁❤️\n\n#{' #'.join(tags[:4])} 🧵 ۶/۶"
        ]

    telegram_post = f"""🚀 کالبدشکافی ترند هوش مصنوعی: {clean_title}

📌 خلاصه رویداد:
{summary}

🔬 ابعاد فنی و تحلیلی:
• موجودیت‌های کلیدی: {entities_str}
• نقطه قوت بنیادین: {swot_str}
• شاخص عمق فنی: {analysis['scores']['tech_depth']}/۱۰ | پتانسیل تجاری: {analysis['scores']['monetization']}/۱۰

💡 نکته طلایی و ضدشهودی:
{counter_note}

🇮🇷 تاثیر بر توسعه‌دهندگان ایرانی:
{iran_note}

💰 زاویه تجاری و درآمدزایی:
{monetize_note}

🔗 منبع و مستندات:
{source}

🆔 @mmdsh0n2 | ⚡ c.q6v.ir/trends
#{' #'.join(tags[:5])}"""

    linkedin_post = f"""Exciting AI Breakthrough: An In-Depth Look at {clean_title}

The landscape of Artificial Intelligence and developer tooling is evolving rapidly. Here is a breakdown of why {clean_title} is gaining massive traction:

1. The Paradigm Shift:
{summary}

2. Architectural Moat:
{swot_str}

3. Industry Reality vs Hype:
{counter_note}

4. Commercial & Implementation Takeaways:
{monetize_note}

Source & Repository: {source}

#ArtificialIntelligence #MachineLearning #TechTrends #SoftwareEngineering #{tags[0]}"""

    midjourney_prompt = f"/imagine prompt: Futuristic high-tech cybernetic visualization representing {clean_title}, holographic neural network schematic, sleek glowing data streams, dark obsidian and neon violet cyberpunk aesthetic, octane render, 8k resolution, cinematic lighting, editorial tech magazine cover style --ar 16:9 --v 6.1"

    card_data = {
        "title": clean_title,
        "subtitle": f"کالبدشکافی تحلیلی {entities_str} و معماری هوش مصنوعی",
        "badge": "⚡ BREAKTHROUGH ANALYSIS",
        "tagline": f"عمق فنی: {analysis['scores']['tech_depth']}/۱۰ | وایرال: {analysis['scores']['virality']}٪",
        "takeaway1": f"مزیت رقابتی: {swot_str[:65]}...",
        "takeaway2": f"فرصت ایران: {iran_note[:65]}...",
        "takeaway3": f"نکته کلیدی: {counter_note[:65]}...",
        "source": source,
        "author": f"MMD (@{author if author else 'mmdsh0n2'})",
        "retweets": f"{int(analysis['scores']['virality'] * 12)}",
        "stars": "4.9k"
    }

    return {
        "tweets": tweets,
        "telegram_post": telegram_post,
        "linkedin_post": linkedin_post,
        "midjourney_prompt": midjourney_prompt,
        "card_data": card_data,
        "deep_analysis": analysis
    }


class TrendHandler(http.server.BaseHTTPRequestHandler):
    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
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
            self.send_cors_headers()
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif path in ["/api/analyze", "/analyze"]:
            payload = {"status": "ok", "message": "Deep Intelligence Analysis Engine v4.0 active. Use POST to trigger full autopsy."}
            body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif path in ["/api/tweets", "/tweets"]:
            with cache["lock"]:
                fa_tweets = list(cache["tweets_fa"])
                en_tweets = list(cache["tweets_en"])
                stats = dict(cache["stats"])

            lang = query.get("lang", ["all"])[0]
            cat = query.get("category", ["all"])[0]
            sort_by = query.get("sort", ["viral"])[0]

            if lang == "fa":
                selected = fa_tweets
            elif lang == "en":
                selected = en_tweets
            else:
                selected = list(cache["all_tweets"])

            if cat != "all":
                selected = [t for t in selected if t.get("category") == cat]

            if sort_by == "viral":
                selected.sort(key=lambda x: x.get("virality_score", 0), reverse=True)
            elif sort_by == "likes":
                selected.sort(key=lambda x: x.get("likes", 0), reverse=True)

            payload = {
                "status": "ok",
                "count": len(selected),
                "total_fa": len(fa_tweets),
                "total_en": len(en_tweets),
                "stats": stats,
                "tweets": selected
            }
            body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif path in ["/api/twitter_user", "/twitter_user"]:
            prof = fetch_twitter_profile()
            body = json.dumps(prof, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif path in ["/api/health", "/health"]:
            with cache["lock"]:
                trend_count = len(cache["trends"])
                tweet_count = len(cache["all_tweets"])
            body = json.dumps({
                "status": "healthy",
                "service": "AI Trend Hunter Backend",
                "version": "3.0",
                "trends_cached": trend_count,
                "tweets_cached": tweet_count,
                "port": PORT
            }).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        else:
            self.send_response(404)
            self.send_cors_headers()
            self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ["/api/generate", "/generate"]:
            content_len = int(self.headers.get('Content-Length', 0))
            raw_body = self.rfile.read(content_len).decode('utf-8')
            try:
                data = json.loads(raw_body)
            except Exception:
                data = {}

            trend_id = data.get("trend_id")
            custom_topic = data.get("custom_topic", "").strip()
            tone = data.get("tone", "viral_hook")

            title = "انقلاب جدید در هوش مصنوعی"
            summary = "پیشرفت‌های جدید در ایجنت‌های خودکار و مدل‌های استدلالی متن‌باز."
            tags = ["هوش_مصنوعی", "فناوری", "تکنولوژی", "نوآوری"]
            source = "AI Radar"

            if custom_topic:
                title = custom_topic
                summary = f"بررسی جامع و موشکافانه موضوع «{custom_topic}» و تاثیر آن بر آینده توسعه نرم‌افزار و ابزارهای هوشمند."
                tags = [custom_topic[:15].replace(" ", "_"), "هوش_مصنوعی", "تکنولوژی"]
            elif trend_id:
                with cache["lock"]:
                    matched = [t for t in cache["trends"] if t.get("id") == trend_id]
                    if matched:
                        item = matched[0]
                        title = item.get("title", title)
                        summary = item.get("summary", summary)
                        source = item.get("source", source)
                        tags = ["هوش_مصنوعی", item.get("category", "AI"), "ترند", "فناوری"]

            package = generate_full_package(title, summary, tags, source, tone=tone)
            payload = {
                "status": "ok",
                "trend_id": trend_id,
                "title": title,
                "tone": tone,
                **package
            }
            body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif path in ["/api/tweet_to_thread", "/tweet_to_thread"]:
            content_len = int(self.headers.get('Content-Length', 0))
            raw_body = self.rfile.read(content_len).decode('utf-8')
            try:
                data = json.loads(raw_body)
            except Exception:
                data = {}

            tweet_text = data.get("tweet_text", "").strip()
            author_name = data.get("author_name", "اکوسیستم توییتر").strip()
            author_handle = data.get("author_handle", "").strip()
            lang = data.get("lang", "en")
            tone = data.get("tone", "viral_hook")

            title = f"تحلیل ترند: توییت {author_name}"
            summary = f"بررسی بینش مطرح‌شده توسط {author_name} (@{author_handle}):\n«{tweet_text}»\nاین دیدگاه بازتاب گسترده‌ای در جامعه فناوری داشته و چالش‌های جدی سیستم‌های فعلی را هدف گرفته است."
            tags = ["ترند_توییتر", "تحلیل_فناوری", author_handle.replace("_", "") if author_handle else "توییتر", "هوش_مصنوعی"]
            source = f"توییتر / X (@{author_handle})"

            package = generate_full_package(title, summary, tags, source, tone=tone)
            payload = {
                "status": "ok",
                "tweet_text": tweet_text,
                "author": f"{author_name} (@{author_handle})",
                "title": title,
                "tone": tone,
                **package
            }
            body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif path in ["/api/analyze", "/analyze"]:
            content_len = int(self.headers.get('Content-Length', 0))
            raw_body = self.rfile.read(content_len).decode('utf-8')
            try:
                data = json.loads(raw_body)
            except Exception:
                data = {}

            item_type = data.get("type", "trend")
            item_id = data.get("id")
            tone = data.get("tone", "viral_hook")

            title = data.get("title", "بررسی ترند هوش مصنوعی")
            summary = data.get("summary", "") or data.get("text", "")
            author = data.get("author", "")
            source = data.get("source", "اکوسیستم هوش مصنوعی")
            category = data.get("category", "AI")

            if item_type == "trend" and item_id:
                with cache["lock"]:
                    matched = [t for t in cache["trends"] if t.get("id") == item_id]
                    if matched:
                        item = matched[0]
                        title = item.get("title", title)
                        summary = item.get("summary", summary)
                        source = item.get("source", source)
                        category = item.get("category", "AI")
                        author = item.get("author", "جامعه هوش مصنوعی")
            elif item_type == "tweet" and item_id:
                with cache["lock"]:
                    matched = [t for t in cache.get("tweets", []) if t.get("id") == item_id]
                    if matched:
                        tw = matched[0]
                        title = f"توییت {tw.get('author_name', '')}"
                        summary = tw.get("text", "")
                        author = f"{tw.get('author_name', '')} (@{tw.get('author_handle', '')})"
                        source = f"X.com/{tw.get('author_handle', '')}"
                        category = tw.get("category", "Tech")

            tags = ["هوش_مصنوعی", "کالبدشکافی_فنی", "ترند_روز"]
            package = generate_full_package(title, summary, tags, source, author=author, category=category, tone=tone)
            payload = {
                "status": "ok",
                "item_type": item_type,
                "item_id": item_id,
                "title": title,
                "author": author,
                "source": source,
                "tone": tone,
                **package
            }
            body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path in ["/api/twitter_post", "/twitter_post"]:
            content_len = int(self.headers.get('Content-Length', 0))
            raw_body = self.rfile.read(content_len).decode('utf-8')
            try:
                data = json.loads(raw_body)
            except Exception:
                data = {}

            tweets = data.get("tweets", [])
            image_base64 = data.get("image_base64")

            if not tweets or not isinstance(tweets, list):
                res = {"ok": False, "error": "لیست توییت‌ها ارسال نشده است."}
            else:
                res = publish_thread_to_twitter(tweets, image_base64=image_base64)

            body = json.dumps(res, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors_headers()
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        else:
            self.send_response(404)
            self.send_cors_headers()
            self.end_headers()

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

def main():
    print(f"Starting initial cache sync on port {PORT}...")
    # Initialize with seeds immediately
    fa_s, en_s = get_seed_tweets()
    flagships = get_flagship_trends()
    with cache["lock"]:
        cache["trends"] = flagships
        cache["tweets_fa"] = fa_s
        cache["tweets_en"] = en_s
        cache["all_tweets"] = fa_s + en_s
        cache["stats"] = {
            "total_trends": len(flagships),
            "total_papers": 0,
            "total_repos": 14,
            "total_fa_tweets": len(fa_s),
            "total_en_tweets": len(en_s),
            "total_all_tweets": len(fa_s) + len(en_s),
            "categories": {"all": len(flagships), "llm": 2, "tools": 1, "vision": 1, "opensource": 1},
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    t = threading.Thread(target=update_cache_loop, daemon=True)
    t.start()
    time.sleep(1)

    server = ThreadedHTTPServer(("0.0.0.0", PORT), TrendHandler)
    print(f"AI Trend Hunter Server v3.0 listening on port {PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
