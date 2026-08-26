import asyncio, json, toml
from datetime import datetime
from pathlib import Path
from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
from weather.weather import Weather
from news.main import News
from tasks.main import Task
from quotes.main import getQuote

console = Console()

# ─── Cache settings ──────────────────────────────────────────────────────────
CACHE_FILE = Path('./').parent / ".dashboard_cache.json"
CACHE_TTL = {
    "weather": 900,      # 15 minutes
    "news": 600,         # 10 minutes
    "quote": 300,        # 5 minutes
}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def condition_emoji(desc: str) -> str:
    d = desc.lower()
    conditions = {
        "sunny": "☀️",
        "clear": "☀️",
        "partly cloudy": "⛅",
        "cloudy": "☁️",
        "overcast": "☁️",
        "rain": "🌧️",
        "drizzle": "🌧️",
        "thunder": "⛈️",
        "storm": "⛈️",
        "snow": "❄️",
        "sleet": "❄️",
        "mist": "🌫️",
        "fog": "🌫️",
        "wind": "💨",
    }
    for key, emoji in conditions.items():
        if key in d:
            return emoji
    return "🌤️"


def format_date(value: str) -> str:
    if not value:
        return "N/A"
    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).strftime("%d %b %H:%M")
    except (ValueError, TypeError):
        return value[:10]


# ─────────────────────────────────────────────────────────────────────────────
# Cache helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_cache():
    """Load cache from disk, return dict or empty."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_cache(cache):
    """Save cache to disk."""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def is_cache_fresh(cache_entry, ttl_seconds):
    """Check if a cached entry is still valid."""
    if not cache_entry or "timestamp" not in cache_entry:
        return False
    try:
        timestamp = datetime.fromisoformat(cache_entry["timestamp"])
        age = (datetime.now() - timestamp).total_seconds()
        return age < ttl_seconds
    except (ValueError, TypeError):
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard Data – with caching
# ─────────────────────────────────────────────────────────────────────────────

class DashboardData:
    def __init__(self):
        self.date = datetime.now().strftime("%A, %B %d")
        self.username = self._get_username()

        self.location = {}
        self.weather_today = {}
        self.weather_tomorrow = {}
        self.news = []
        self.calendar = []
        self.quote = {"text": "Loading...", "author": ""}
        self.last_updated = ""

        # Load saved cache
        self._cache = load_cache()

    def _get_username(self) -> str:
        file = Path(__file__).parent.parent / "setting.toml"
        try:
            with open(file, encoding="utf-8") as f:
                return toml.load(f).get("user", {}).get("name", "User")
        except (FileNotFoundError, toml.TomlDecodeError):
            return "User"

    def _getTasks(self):
        try:
            task_manager = Task()
            tasks_dict = task_manager.returnTasks()
            if tasks_dict and isinstance(tasks_dict, dict):
                self.calendar = sorted(tasks_dict.items())
            else:
                self.calendar = []
        except Exception:
            self.calendar = []

    # ─── Individual fetch methods with caching ────────────────────────

    async def _get_weather(self, force=False):
        """Fetch weather, using cache if fresh (unless force=True)."""
        if not force and is_cache_fresh(self._cache.get("weather"), CACHE_TTL["weather"]):
            # Restore from cache
            w = self._cache["weather"]
            self.location = w.get("location", {})
            self.weather_today = w.get("today", {})
            self.weather_tomorrow = w.get("tomorrow", {})
            return

        # Fetch fresh
        try:
            data = await Weather().makeCall()
            if data:
                self.location = data.get("location", {})
                self.weather_today = data.get("today", {})
                self.weather_tomorrow = data.get("tomorrow", {})
                # Save to cache
                self._cache["weather"] = {
                    "location": self.location,
                    "today": self.weather_today,
                    "tomorrow": self.weather_tomorrow,
                    "timestamp": datetime.now().isoformat(),
                }
                save_cache(self._cache)
                return
        except Exception as e:
            console.print(f"[red]Weather error: {e}[/]")

        # Fallback
        self.location = {"city": "Unknown", "region": "Unknown", "country": "Unknown"}
        self.weather_today = {
            "temp_C": "--",
            "feels_like_C": "--",
            "weather_desc": "No data",
            "humidity": "--",
            "cloudcover": "--",
            "uvIndex": "--",
            "visibility_km": "--",
            "observation_time": "--",
        }
        self.weather_tomorrow = {
            "weather_desc": "No forecast",
            "max_temp_C": "--",
            "min_temp_C": "--",
        }

    async def _get_news(self, force=False):
        if not force and is_cache_fresh(self._cache.get("news"), CACHE_TTL["news"]):
            self.news = self._cache["news"].get("articles", [])
            return

        try:
            articles = await News().makeCall()
            self.news = articles[:3] if articles else []
            self._cache["news"] = {
                "articles": self.news,
                "timestamp": datetime.now().isoformat(),
            }
            save_cache(self._cache)
        except Exception as e:
            console.print(f"[red]News error: {e}[/]")
            self.news = []

    async def _get_quote(self, force=False):
        if not force and is_cache_fresh(self._cache.get("quote"), CACHE_TTL["quote"]):
            self.quote = self._cache["quote"].get("data", {})
            return

        try:
            q, a = await getQuote()
            self.quote = {"text": q, "author": a}
            self._cache["quote"] = {
                "data": self.quote,
                "timestamp": datetime.now().isoformat(),
            }
            save_cache(self._cache)
        except Exception as e:
            console.print(f"[red]Quote error: {e}[/]")
            self.quote = {"text": "Could not load quote", "author": "unknown"}

    async def refresh(self, force=False):
        """Refresh all data – respects cache unless force=True."""
        await asyncio.gather(
            self._get_weather(force),
            self._get_news(force),
            self._get_quote(force),
        )
        self._getTasks()
        self.last_updated = datetime.now().strftime("%H:%M")


# ─────────────────────────────────────────────────────────────────────────────
# Rendering functions – unchanged
# ─────────────────────────────────────────────────────────────────────────────

def render_header(data):
    return Panel(
        Align.center(
            f"[bold cyan]PERSONAL DASHBOARD[/]\n"
            f"[white]{data.date}[/]"
        ),
        box=box.HEAVY,
        border_style="cyan",
        padding=(0, 1),
    )


def render_greeting(data):
    return Panel(
        Align.center(
            f"[bold yellow]Hello, {data.username}![/]"
        ),
        box=box.SIMPLE,
        border_style="yellow",
        padding=(0, 1),
    )


def render_weather(data):
    loc = data.location
    today = data.weather_today
    tomorrow = data.weather_tomorrow

    city = loc.get("city", "Unknown")
    region = loc.get("region", "")
    country = loc.get("country", "")

    desc = today.get("weather_desc", "N/A")
    icon = condition_emoji(desc)

    today_text = Text()
    today_text.append(f"{icon} {desc}\n", style="bold white")
    today_text.append(f"{today.get('temp_C', '--')}°C ", style="bold cyan")
    today_text.append(f"(feels {today.get('feels_like_C', '--')}°C)\n", style="dim")
    today_text.append(
        f"Humidity: {today.get('humidity', '--')}%\n"
        f"Clouds: {today.get('cloudcover', '--')}%\n"
        f"UV: {today.get('uvIndex', '--')}\n"
        f"Visibility: {today.get('visibility_km', '--')} km",
        style="white"
    )
    today_panel = Panel(
        today_text,
        title="TODAY",
        border_style="blue",
        padding=(0, 1),
        expand=True,
    )

    tomorrow_desc = tomorrow.get("weather_desc", "No forecast")
    tomorrow_text = Text()
    tomorrow_text.append(f"{condition_emoji(tomorrow_desc)} {tomorrow_desc}\n", style="bold white")
    tomorrow_text.append(f"High: {tomorrow.get('max_temp_C', '--')}°C\n", style="green")
    tomorrow_text.append(f"Low: {tomorrow.get('min_temp_C', '--')}°C", style="blue")
    tomorrow_panel = Panel(
        tomorrow_text,
        title="TOMORROW",
        border_style="cyan",
        padding=(0, 1),
        expand=True,
    )

    content = Layout()
    content.split_row(
        Layout(today_panel),
        Layout(tomorrow_panel),
    )

    location = (
        f"[bold]{city}[/]"
        f"{f', {region}' if region else ''}"
        f"{f', {country}' if country else ''}"
    )

    return Panel(
        Group(
            Align.center(location),
            content,
        ),
        title="☀ WEATHER",
        title_align="left",
        border_style="blue",
        padding=(1, 1),
        expand=True,
    )


def render_news(articles):
    if not articles:
        return Panel(
            Align.center("[dim]No news available.[/]"),
            title="📰 TOP 3 NEWS",
            border_style="green",
            expand=True,
        )

    blocks = []
    for index, article in enumerate(articles[:3], 1):
        title = article.get("title", "No title")
        source = article.get("source", {}).get("name", "Unknown")
        date = format_date(article.get("publishedAt", ""))
        description = article.get("description", "")
        url = article.get("url", "")

        text = Text()
        text.append(f"{index}. ", style="bold cyan")
        if url:
            text.append(title, style=f"bold white link {url}")
        else:
            text.append(title, style="bold white")
        text.append(f"\n   {source} · {date}", style="dim")
        if description:
            text.append(f"\n   {description}", style="grey70")
        if url:
            text.append("\n   🔗 ", style="dim")
            text.append(url, style=f"underline cyan link {url}")
        blocks.append(text)

    return Panel(
        Group(*blocks),
        title="📰 TOP 3 NEWS",
        title_align="left",
        border_style="green",
        padding=(1, 2),
        expand=True,
    )


def render_calendar(data):
    if not data.calendar:
        return Panel(
            Align.center("[dim]No tasks for today.[/]"),
            title="📅 TODAY",
            border_style="magenta",
            expand=True,
        )

    table = Table(show_header=False, box=None, expand=True)
    table.add_column(style="cyan", no_wrap=True)
    table.add_column(style="white", ratio=1)

    for time, event in data.calendar:
        table.add_row(time, event)

    return Panel(
        table,
        title="📅 TODAY",
        border_style="magenta",
        padding=(1, 1),
        expand=True,
    )


def render_quote(data):
    return Panel(
        Align.center(
            f'[italic white]"{data.quote["text"]}"[/]\n'
            f'[dim]— {data.quote["author"]}[/]',
            vertical="middle",
        ),
        title="💡 QUOTE",
        border_style="yellow",
        padding=(1, 2),
        expand=True,
    )


def render_footer(data):
    return Panel(
        Align.center(
            f"[dim]Updated: {data.last_updated} | "
            "Type 'help' for commands[/]"
        ),
        box=box.SIMPLE,
        border_style="grey50",
        padding=(0, 1),
    )


def render_dashboard(data):
    layout = Layout()
    layout.split(
        Layout(render_header(data), size=4),
        Layout(render_greeting(data), size=3),
        Layout(render_weather(data), size=10),
        Layout(render_news(data.news), name="news", ratio=4),
        Layout(name="bottom", size=6),
        Layout(render_footer(data), size=3),
    )
    layout["bottom"].split_row(
        Layout(render_calendar(data), ratio=1),
        Layout(render_quote(data), ratio=1),
    )
    console.clear()
    console.print(layout)


# ─────────────────────────────────────────────────────────────────────────────
# Help – added 'force' command
# ─────────────────────────────────────────────────────────────────────────────

def show_help():
    console.print(
        Panel(
            "[bold]Commands[/]\n\n"
            "[cyan]w[/] / weather       Weather\n"
            "[cyan]n[/] / news          Top 3 news\n"
            "[cyan]cal[/] / calendar    Calendar\n"
            "[cyan]add[/] / a           Add a new task\n"
            "[cyan]r[/] / refresh       Refresh (use cache if fresh)\n"
            "[cyan]f[/] / force         Force refresh (bypass cache)\n"
            "[cyan]h[/] / help          Help\n"
            "[cyan]q[/] / exit          Exit",
            title="HELP",
            border_style="green",
            padding=(1, 2),
        )
    )


# ─────────────────────────────────────────────────────────────────────────────
# Add Task
# ─────────────────────────────────────────────────────────────────────────────

def add_task():
    console.print("\n[bold yellow]Add a new task[/]\n")

    description = Prompt.ask("[cyan]Task description[/]")
    if not description.strip():
        console.print("[red]Task description cannot be empty.[/]")
        return

    time_str = Prompt.ask("[cyan]Time (HH:MM)[/]", default="00:00")
    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        console.print("[red]Invalid time format. Use HH:MM[/]")
        return

    try:
        task_mgr = Task()
        task_mgr.addTask(time_str, description)
        console.print("[green]Task added successfully![/]")
    except AttributeError:
        console.print("[red]Task.addTask() not found. Check your Task class.[/]")
    except Exception as e:
        console.print(f"[red]Error adding task: {e}[/]")


# ─────────────────────────────────────────────────────────────────────────────
# Command Loop – with caching support
# ─────────────────────────────────────────────────────────────────────────────

def run_dashboard():
    data = DashboardData()

    # Initial refresh – use cache if available
    try:
        asyncio.run(data.refresh(force=False))
    except KeyboardInterrupt:
        console.print("\n[bold cyan]Goodbye![/]")
        return

    try:
        while True:
            render_dashboard(data)

            try:
                cmd = Prompt.ask("[bold cyan]Command[/]").strip().lower()
            except KeyboardInterrupt:
                console.print("\n[bold cyan]Goodbye![/]")
                return

            if cmd in ("q", "quit", "exit"):
                console.clear()
                console.print("[bold cyan]Goodbye![/]")
                break

            # Normal refresh (respects cache)
            if cmd in ("r", "refresh"):
                try:
                    asyncio.run(data.refresh(force=False))
                except KeyboardInterrupt:
                    console.print("\n[bold yellow]Refresh cancelled.[/]")
                    input("\nPress Enter to continue...")
                continue

            # Force refresh (bypass cache)
            if cmd in ("f", "force"):
                try:
                    asyncio.run(data.refresh(force=True))
                except KeyboardInterrupt:
                    console.print("\n[bold yellow]Force refresh cancelled.[/]")
                    input("\nPress Enter to continue...")
                continue

            if cmd in ("add", "a"):
                add_task()
                try:
                    asyncio.run(data.refresh(force=False))
                except KeyboardInterrupt:
                    console.print("\n[bold yellow]Refresh cancelled after adding task.[/]")
                    input("\nPress Enter to continue...")
                continue

            if cmd in ("n", "news"):
                console.clear()
                console.print(render_news(data.news))
                try:
                    input("\nPress Enter to continue...")
                except KeyboardInterrupt:
                    console.print("\n[bold cyan]Goodbye![/]")
                    return
                continue

            if cmd in ("w", "weather"):
                console.clear()
                console.print(render_weather(data))
                try:
                    input("\nPress Enter to continue...")
                except KeyboardInterrupt:
                    console.print("\n[bold cyan]Goodbye![/]")
                    return
                continue

            if cmd in ("cal", "calendar"):
                console.clear()
                console.print(render_calendar(data))
                try:
                    input("\nPress Enter to continue...")
                except KeyboardInterrupt:
                    console.print("\n[bold cyan]Goodbye![/]")
                    return
                continue

            if cmd in ("h", "help", "?"):
                console.clear()
                show_help()
                try:
                    input("\nPress Enter to continue...")
                except KeyboardInterrupt:
                    console.print("\n[bold cyan]Goodbye![/]")
                    return
                continue

            console.print(f"[red]Unknown command: {cmd}[/]")
            try:
                input("\nPress Enter to continue...")
            except KeyboardInterrupt:
                console.print("\n[bold cyan]Goodbye![/]")
                return

    except KeyboardInterrupt:
        console.print("\n[bold cyan]Goodbye![/]")
    finally:
        pass

if __name__ == "__main__":
    run_dashboard()
