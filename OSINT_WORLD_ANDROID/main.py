import sqlite3, hashlib, secrets, string, threading
from datetime import datetime
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.core.window import Window

DB = "osint_world_android.db"
BG = (0.025, 0.08, 0.17, 1)
PANEL = (0.04, 0.13, 0.25, 1)
BLUE = (0.03, 0.49, 0.94, 1)
WHITE = (0.95, 0.98, 1, 1)
MUTED = (0.57, 0.66, 0.75, 1)
GREEN = (0.10, 0.86, 0.57, 1)
RED = (0.90, 0.35, 0.40, 1)

FIRST = ["Алексей","Максим","Илья","Даниил","Кирилл","Артём","Никита","Роман","Егор","Михаил"]
LAST = ["Волков","Орлов","Соколов","Морозов","Крылов","Лебедев","Воронцов","Белов","Фёдоров","Зайцев"]
CITIES = ["Нордград","Белогорск","Северный","Луговой","Архангельск"]

def db():
    return sqlite3.connect(DB)

def hp(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def init_db():
    con = db(); c = con.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY, game_id TEXT UNIQUE, username TEXT UNIQUE,
        password TEXT, role TEXT DEFAULT 'user', level INTEGER DEFAULT 1,
        xp INTEGER DEFAULT 0, balance INTEGER DEFAULT 200,
        phone TEXT DEFAULT '', anonymity INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS profiles(
        user_id INTEGER PRIMARY KEY, nickname TEXT, phone TEXT, username TEXT,
        first_name TEXT, last_name TEXT, city TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS inventory(
        id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, item_type TEXT,
        quantity INTEGER DEFAULT 1, storage_tb INTEGER DEFAULT 1, anonymity INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS market(
        id INTEGER PRIMARY KEY, name TEXT, item_type TEXT, price INTEGER,
        storage_tb INTEGER, anonymity INTEGER, quantity INTEGER, description TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS tasks(
        id INTEGER PRIMARY KEY, title TEXT, target TEXT, reward INTEGER,
        claimed_by INTEGER DEFAULT 0, search_done INTEGER DEFAULT 0,
        takedown_done INTEGER DEFAULT 0, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY, user_id INTEGER, username TEXT, text TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS takedowns(
        id INTEGER PRIMARY KEY, actor_id INTEGER, target TEXT, created_at TEXT)""")
    c.execute("SELECT id FROM users WHERE username='admin'")
    if not c.fetchone():
        gid = "OW-ADMIN01"
        c.execute("INSERT INTO users(game_id,username,password,role,level,xp,balance,anonymity) VALUES(?,?,?,?,?,?,?,?)",
                  (gid,"admin",hp("admin123"),"admin",10,5000,50000,100))
        uid = c.lastrowid
        c.execute("INSERT INTO profiles(user_id,nickname,phone,username,first_name,last_name,city) VALUES(?,?,?,?,?,?,?)",
                  (uid,"admin","","admin","Admin","OSINT","Нордград"))
    seeds = [
        ("Cipher Vault","Поиск информации",300,2,4,10,"Игровой терминал поиска."),
        ("Ghost Console","Поиск информации",650,5,7,5,"Улучшенный игровой терминал."),
        ("Null Protocol","Снос",900,1,9,3,"Сценарий игрового сноса."),
        ("Atlas Database","База данных",450,20,5,20,"Вымышленная игровая база."),
        ("Ghost Database","База данных",1100,50,8,10,"Большая вымышленная база."),
        ("Clean Sweep","Снос программа",750,5,7,10,"Игровая программа сноса.")
    ]
    for row in seeds:
        c.execute("SELECT id FROM market WHERE name=?", (row[0],))
        if not c.fetchone():
            c.execute("INSERT INTO market(name,item_type,price,storage_tb,anonymity,quantity,description) VALUES(?,?,?,?,?,?,?)", row)
    con.commit(); con.close()

def make_task():
    con=db(); c=con.cursor()
    c.execute("SELECT username FROM users WHERE username!='admin' ORDER BY RANDOM() LIMIT 1")
    r=c.fetchone()
    if not r:
        target = "ghost_" + secrets.token_hex(3)
        gid = "OW-" + secrets.token_hex(4).upper()
        pw = hp(secrets.token_urlsafe(8))
        c.execute("INSERT OR IGNORE INTO users(game_id,username,password) VALUES(?,?,?)",(gid,target,pw))
        uid=c.lastrowid
        c.execute("INSERT OR IGNORE INTO profiles(user_id,nickname,phone,username,first_name,last_name,city) VALUES(?,?,?,?,?,?,?)",
                  (uid,target,"",target,secrets.choice(FIRST),secrets.choice(LAST),secrets.choice(CITIES)))
    else:
        target=r[0]
    reward=secrets.choice([150,250,350,500,750])
    c.execute("INSERT INTO tasks(title,target,reward,created_at) VALUES(?,?,?,?)",
              ("Найти и обработать цель",target,reward,datetime.now().isoformat(timespec="seconds")))
    con.commit(); con.close()

class Base(Screen):
    def title(self, text):
        b=BoxLayout(size_hint_y=None,height=dp(54),padding=dp(10))
        l=Label(text=text,font_size=dp(21),bold=True,color=WHITE,halign="left",valign="middle")
        b.add_widget(l); return b
    def btn(self,text,cb=None):
        b=Button(text=text,size_hint_y=None,height=dp(50),background_normal="",background_color=PANEL,
                 color=WHITE,font_size=dp(15))
        if cb: b.bind(on_release=cb)
        return b
    def body(self):
        box=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(8))
        return box
    def msg(self,text,title="OSINT WORLD"):
        Popup(title=title,content=Label(text=text,color=WHITE,text_size=(dp(280),None)),
              size_hint=(.86,.42)).open()

class Login(Base):
    def on_enter(self):
        self.clear_widgets()
        box=self.body()
        box.add_widget(Label(text="OSINT WORLD",font_size=dp(32),bold=True,color=BLUE,size_hint_y=None,height=dp(80)))
        self.user=TextInput(hint_text="Никнейм",multiline=False,size_hint_y=None,height=dp(50))
        self.pw=TextInput(hint_text="Пароль",password=True,multiline=False,size_hint_y=None,height=dp(50))
        box.add_widget(self.user); box.add_widget(self.pw)
        box.add_widget(self.btn("ВОЙТИ",self.login))
        box.add_widget(self.btn("РЕГИСТРАЦИЯ",lambda *_: setattr(self.manager,"current","register")))
        self.add_widget(box)
    def login(self,*_):
        con=db(); r=con.execute("SELECT id FROM users WHERE username=? AND password=?",(self.user.text.strip(),hp(self.pw.text))).fetchone(); con.close()
        if not r: self.msg("Неверный никнейм или пароль","Ошибка"); return
        app=App.get_running_app(); app.uid=r[0]; app.username=self.user.text.strip()
        self.manager.current="home"

class Register(Login):
    def on_enter(self):
        self.clear_widgets(); box=self.body()
        box.add_widget(Label(text="Создание аккаунта",font_size=dp(26),bold=True,color=WHITE,size_hint_y=None,height=dp(70)))
        self.user=TextInput(hint_text="Никнейм",multiline=False,size_hint_y=None,height=dp(50))
        self.pw=TextInput(hint_text="Пароль",password=True,multiline=False,size_hint_y=None,height=dp(50))
        box.add_widget(self.user); box.add_widget(self.pw); box.add_widget(self.btn("СОЗДАТЬ",self.register))
        box.add_widget(self.btn("НАЗАД",lambda *_: setattr(self.manager,"current","login")))
        self.add_widget(box)
    def register(self,*_):
        u=self.user.text.strip(); p=self.pw.text
        if len(u)<3 or len(p)<4: self.msg("Ник минимум 3 символа, пароль минимум 4.","Ошибка"); return
        con=db()
        try:
            gid="OW-"+secrets.token_hex(4).upper()
            con.execute("INSERT INTO users(game_id,username,password) VALUES(?,?,?)",(gid,u,hp(p)))
            uid=con.execute("SELECT id FROM users WHERE username=?",(u,)).fetchone()[0]
            con.execute("INSERT INTO profiles(user_id,nickname,phone,username,first_name,last_name,city) VALUES(?,?,?,?,?,?,?)",
                        (uid,u,"",u,secrets.choice(FIRST),secrets.choice(LAST),secrets.choice(CITIES)))
            con.commit()
        except sqlite3.IntegrityError:
            con.close(); self.msg("Такой ник уже занят.","Ошибка"); return
        con.close(); self.msg("Аккаунт создан."); self.manager.current="login"

class Home(Base):
    def on_enter(self):
        self.clear_widgets(); app=App.get_running_app(); box=self.body()
        r=db().execute("SELECT level,xp,balance,anonymity,role FROM users WHERE id=?",(app.uid,)).fetchone()
        box.add_widget(self.title("OSINT WORLD"))
        box.add_widget(Label(text=f"@{app.username}   •   LVL {r[0]}   •   ${r[2]}   •   Анонимность {r[3]}%",color=WHITE,size_hint_y=None,height=dp(38)))
        grid=GridLayout(cols=2,spacing=dp(8),size_hint_y=None); grid.bind(minimum_height=grid.setter("height"))
        items=[("👤 Профиль","profile"),("💬 Чат","chat"),("📋 Задания","tasks"),("🛒 Магазин","market"),
               ("🛡 Анонимность","anon"),("📁 Файлы","files"),("🔎 Поиск информации","search"),("🔴 Снос","takedown")]
        for text,s in items:
            grid.add_widget(self.btn(text,lambda *_ ,s=s:setattr(self.manager,"current",s)))
        if r[4]=="admin":
            grid.add_widget(self.btn("⚙ ADMIN CENTER",lambda *_: setattr(self.manager,"current","admin")))
        box.add_widget(grid); box.add_widget(self.btn("ВЫЙТИ",lambda *_: setattr(self.manager,"current","login")))
        self.add_widget(box)

class Profile(Base):
    def on_enter(self):
        self.clear_widgets(); app=App.get_running_app(); con=db()
        r=con.execute("""SELECT u.game_id,u.username,u.phone,u.level,u.xp,u.balance,u.anonymity,u.role,
                         p.first_name,p.last_name,p.city FROM users u LEFT JOIN profiles p ON p.user_id=u.id WHERE u.id=?""",(app.uid,)).fetchone(); con.close()
        box=self.body(); box.add_widget(self.title("👤 Профиль"))
        box.add_widget(Label(text=f"Ник\n{r[1]}\n\nНомер\n{r[2] or 'Не выдан'}\n\nЮзернейм\n@{r[1]}\n\nGame ID\n{r[0]}\n\nУровень {r[3]}  •  XP {r[4]}\nБаланс ${r[5]}\nАнонимность {r[6]}%\nРоль: {r[7]}",color=WHITE,font_size=dp(17),halign="left",valign="top"))
        box.add_widget(self.btn("НАЗАД",lambda *_: setattr(self.manager,"current","home"))); self.add_widget(box)

class Chat(Base):
    def on_enter(self):
        self.clear_widgets(); box=self.body(); box.add_widget(self.title("💬 Общий чат"))
        sv=ScrollView(); labels=BoxLayout(orientation="vertical",spacing=dp(6),size_hint_y=None); labels.bind(minimum_height=labels.setter("height"))
        con=db(); rows=con.execute("SELECT username,text,created_at FROM messages ORDER BY id DESC LIMIT 80").fetchall(); con.close()
        for u,t,tm in reversed(rows):
            labels.add_widget(Label(text=f"[{tm[11:16]}] @{u}: {t}",color=WHITE,size_hint_y=None,height=dp(34),halign="left"))
        sv.add_widget(labels); box.add_widget(sv)
        row=BoxLayout(size_hint_y=None,height=dp(50),spacing=dp(6)); self.inp=TextInput(hint_text="Сообщение",multiline=False); row.add_widget(self.inp); row.add_widget(self.btn("ОТПРАВИТЬ",self.send)); box.add_widget(row)
        box.add_widget(self.btn("НАЗАД",lambda *_: setattr(self.manager,"current","home"))); self.add_widget(box)
    def send(self,*_):
        t=self.inp.text.strip()
        if t:
            con=db(); con.execute("INSERT INTO messages(user_id,username,text,created_at) VALUES(?,?,?,?)",(App.get_running_app().uid,App.get_running_app().username,t,datetime.now().isoformat(timespec="seconds"))); con.commit(); con.close()
            self.on_enter()

class Tasks(Base):
    def on_enter(self):
        self.clear_widgets(); box=self.body(); box.add_widget(self.title("📋 Задания"))
        sv=ScrollView(); lay=BoxLayout(orientation="vertical",spacing=dp(10),size_hint_y=None); lay.bind(minimum_height=lay.setter("height"))
        con=db(); rows=con.execute("SELECT id,title,target,reward,claimed_by,search_done,takedown_done FROM tasks ORDER BY id DESC").fetchall(); con.close()
        for row in rows:
            tid,title,target,reward,claimed,sd,td=row
            card=BoxLayout(orientation="vertical",padding=dp(8),spacing=dp(5),size_hint_y=None,height=dp(150))
            status="Доступно" if not claimed else ("Поиск ✓" if not sd else ("Снос ✓" if not td else "Готово"))
            card.add_widget(Label(text=f"{title}\nЦель: {target if claimed else '???'}\nНаграда: ${reward}\nСтатус: {status}",color=WHITE,halign="left"))
            if not claimed: card.add_widget(self.btn("ВЗЯТЬСЯ ЗА ЗАДАНИЕ",lambda *_ ,tid=tid:self.claim(tid)))
            elif sd and td: card.add_widget(self.btn("✓ ЗАДАНИЕ ВЫПОЛНЕНО",lambda *_ ,tid=tid:self.complete(tid)))
            else: card.add_widget(self.btn("ОБНОВИТЬ СТАТУС",lambda *_: self.on_enter()))
            lay.add_widget(card)
        sv.add_widget(lay); box.add_widget(sv); box.add_widget(self.btn("НАЗАД",lambda *_: setattr(self.manager,"current","home"))); self.add_widget(box)
    def claim(self,tid):
        con=db(); con.execute("UPDATE tasks SET claimed_by=? WHERE id=? AND claimed_by=0",(App.get_running_app().uid,tid)); con.commit(); con.close(); self.on_enter()
    def complete(self,tid):
        con=db(); r=con.execute("SELECT reward FROM tasks WHERE id=? AND claimed_by=? AND search_done=1 AND takedown_done=1",(tid,App.get_running_app().uid)).fetchone()
        if r:
            con.execute("UPDATE users SET xp=xp+?,balance=balance+? WHERE id=?",(r[0],r[0],App.get_running_app().uid)); con.execute("DELETE FROM tasks WHERE id=?",(tid,)); con.commit()
        con.close(); self.on_enter()

class Market(Base):
    def on_enter(self):
        self.clear_widgets(); box=self.body(); box.add_widget(self.title("🛒 Магазин"))
        sv=ScrollView(); lay=BoxLayout(orientation="vertical",spacing=dp(8),size_hint_y=None); lay.bind(minimum_height=lay.setter("height"))
        con=db(); rows=con.execute("SELECT id,name,item_type,price,storage_tb,anonymity,quantity,description FROM market WHERE quantity>0").fetchall(); con.close()
        for r in rows:
            text=f"{r[1]}\n{r[2]} • ${r[3]} • {r[4]} TB • +{r[5]} anon\n{r[6]} шт. — {r[7]}"
            card=BoxLayout(orientation="vertical",size_hint_y=None,height=dp(125),padding=dp(6)); card.add_widget(Label(text=text,color=WHITE,halign="left")); card.add_widget(self.btn("КУПИТЬ",lambda *_ ,r=r:self.buy(r))); lay.add_widget(card)
        sv.add_widget(lay); box.add_widget(sv); box.add_widget(self.btn("НАЗАД",lambda *_: setattr(self.manager,"current","home"))); self.add_widget(box)
    def buy(self,r):
        con=db(); bal=con.execute("SELECT balance FROM users WHERE id=?",(App.get_running_app().uid,)).fetchone()[0]
        if bal<r[3]: con.close(); self.msg("Недостаточно игровой валюты.","Магазин"); return
        con.execute("UPDATE users SET balance=balance-? WHERE id=?",(r[3],App.get_running_app().uid))
        con.execute("UPDATE market SET quantity=quantity-1 WHERE id=?",(r[0],))
        con.execute("INSERT INTO inventory(user_id,name,item_type,quantity,storage_tb,anonymity) VALUES(?,?,?,?,?,?)",(App.get_running_app().uid,r[1],r[2],1,r[4],r[5]))
        con.commit(); con.close(); self.msg(f"Куплено: {r[1]}"); self.on_enter()

class Anon(Base):
    def on_enter(self):
        self.clear_widgets(); box=self.body(); box.add_widget(self.title("🛡 Анонимность"))
        con=db(); cur=con.execute("SELECT balance,anonymity FROM users WHERE id=?",(App.get_running_app().uid,)).fetchone(); con.close()
        box.add_widget(Label(text=f"Текущий уровень: {cur[1]}%\nБаланс: ${cur[0]}\n\n1% стоит $2.\nМаксимум: 1000%.",color=WHITE,font_size=dp(18)))
        inp=TextInput(hint_text="Сколько процентов купить?",input_filter="int",multiline=False,size_hint_y=None,height=dp(50)); box.add_widget(inp)
        box.add_widget(self.btn("КУПИТЬ",lambda *_:self.buy(inp.text)))
        box.add_widget(self.btn("НАЗАД",lambda *_:setattr(self.manager,"current","home"))); self.add_widget(box)
    def buy(self,n):
        try:n=int(n)
        except:self.msg("Введите число.");return
        con=db(); bal,an=con.execute("SELECT balance,anonymity FROM users WHERE id=?",(App.get_running_app().uid,)).fetchone()
        if n<1 or an+n>1000:self.msg("Допустимо до 1000%.");con.close();return
        # Простая игровая формула: каждый следующий процент ×10 относительно предыдущего.
        # Стоимость считается безопасно с ограничением по игровому балансу.
        cost=sum(2*(10**i) for i in range(n))
        if cost>bal:self.msg("Недостаточно игровой валюты.");con.close();return
        con.execute("UPDATE users SET balance=balance-?,anonymity=anonymity+? WHERE id=?",(cost,n,App.get_running_app().uid));con.commit();con.close();self.msg(f"Куплено {n}%. Стоимость ${cost}.");self.on_enter()

class Files(Base):
    def on_enter(self):
        self.clear_widgets(); box=self.body(); box.add_widget(self.title("📁 Файлы"))
        con=db(); rows=con.execute("SELECT name,item_type,quantity,storage_tb,anonymity FROM inventory WHERE user_id=?",(App.get_running_app().uid,)).fetchall(); con.close()
        for r in rows:
            box.add_widget(Label(text=f"📄 {r[0]}   [{r[1]}]\n{r[2]} шт. • {r[3]} TB • anon {r[4]}",color=WHITE,size_hint_y=None,height=dp(55),halign="left"))
        if not rows: box.add_widget(Label(text="Папка пуста. Купленные предметы появятся автоматически.",color=MUTED))
        box.add_widget(self.btn("НАЗАД",lambda *_:setattr(self.manager,"current","home"))); self.add_widget(box)

class Terminal(Base):
    mode="search"
    def on_enter(self):
        self.clear_widgets(); box=self.body()
        title="🔎 INFORMATION TERMINAL" if self.mode=="search" else "🔴 TAKEDOWN TERMINAL"
        box.add_widget(self.title(title))
        box.add_widget(Label(text=("Введи игровой никнейм и нажми ENTER.\nРезультат — только синтетические данные мира игры."
                                   if self.mode=="search" else "Введи игровой никнейм и нажми ENTER.\nБудет запущена игровая симуляция."),
                             color=MUTED,size_hint_y=None,height=dp(70)))
        self.inp=TextInput(hint_text="Игровой никнейм",multiline=False,size_hint_y=None,height=dp(50))
        self.inp.bind(on_text_validate=self.run); box.add_widget(self.inp); box.add_widget(self.btn("ENTER",self.run))
        self.out=Label(text="> _",color=GREEN,font_size=dp(15),halign="left",valign="top"); box.add_widget(self.out)
        box.add_widget(self.btn("НАЗАД",lambda *_:setattr(self.manager,"current","home"))); self.add_widget(box)
    def run(self,*_):
        target=self.inp.text.strip()
        if not target:return
        con=db(); uid=App.get_running_app().uid
        task=con.execute("SELECT id FROM tasks WHERE claimed_by=? AND target=? ORDER BY id DESC LIMIT 1",(uid,target)).fetchone()
        user=con.execute("""SELECT u.id,u.game_id,u.username,u.level,u.role,p.first_name,p.last_name,p.city
                            FROM users u LEFT JOIN profiles p ON p.user_id=u.id WHERE u.username=?""",(target,)).fetchone()
        if not user:
            con.close(); self.out.text="> ОШИБКА: игровой аккаунт не найден."; return
        if self.mode=="search":
            con.execute("UPDATE tasks SET search_done=1 WHERE claimed_by=? AND target=?",(uid,target))
            con.commit(); con.close()
            self.out.text=f"> SEARCH OK\n> НИК: {user[2]}\n> GAME ID: {user[1]}\n> ФИО: {user[5]} {user[6]}\n> ГОРОД: {user[7]}\n> УРОВЕНЬ: {user[3]}\n> РОЛЬ: {user[4]}\n> [СИНТЕТИЧЕСКИЙ ИГРОВОЙ ПРОФИЛЬ]"
        else:
            if not task: con.close(); self.out.text="> Для сноса сначала возьми задание и выполни поиск."; return
            con.execute("UPDATE tasks SET takedown_done=1 WHERE claimed_by=? AND target=?",(uid,target))
            con.execute("INSERT INTO takedowns(actor_id,target,created_at) VALUES(?,?,?)",(uid,target,datetime.now().isoformat(timespec="seconds"))); con.commit(); con.close()
            self.out.text=f"> TARGET: {target}\n> SIMULATION: 100%\n> TAKEDOWN COMPLETE ✓\n> Только внутриигровая симуляция."

class Admin(Base):
    def on_enter(self):
        self.clear_widgets(); box=self.body(); box.add_widget(self.title("⚙ ADMIN CENTER"))
        con=db(); role=con.execute("SELECT role FROM users WHERE id=?",(App.get_running_app().uid,)).fetchone()[0]; con.close()
        if role!="admin":
            box.add_widget(Label(text="Доступ запрещён.",color=RED)); self.add_widget(box); return
        box.add_widget(self.btn("ВЫДАТЬ НОМЕР",self.give_phone))
        box.add_widget(self.btn("ВЫДАТЬ ВАЛЮТУ",self.give_money))
        box.add_widget(self.btn("НАЗАД",lambda *_:setattr(self.manager,"current","home"))); self.add_widget(box)
    def give_phone(self,*_):
        self.admin_input("Ник игрока","Номер",self.do_phone)
    def give_money(self,*_):
        self.admin_input("Ник игрока","Сумма",self.do_money)
    def admin_input(self,a,b,cb):
        lay=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(8))
        u=TextInput(hint_text=a,multiline=False,size_hint_y=None,height=dp(48)); v=TextInput(hint_text=b,multiline=False,size_hint_y=None,height=dp(48))
        lay.add_widget(u);lay.add_widget(v);lay.add_widget(self.btn("ПОДТВЕРДИТЬ",lambda *_:cb(u.text.strip(),v.text.strip(),lay)))
        pop=Popup(title="Admin Center",content=lay,size_hint=(.9,.55)); lay._popup=pop; pop.open()
    def do_phone(self,u,v,lay):
        con=db(); r=con.execute("SELECT id FROM users WHERE username=?",(u,)).fetchone()
        if r: con.execute("UPDATE users SET phone=? WHERE id=?",(v,r[0])); con.execute("UPDATE profiles SET phone=? WHERE user_id=?",(v,r[0])); con.commit()
        con.close(); lay._popup.dismiss(); self.msg("Номер выдан." if r else "Игрок не найден.")
    def do_money(self,u,v,lay):
        try:n=int(v)
        except: lay._popup.dismiss(); self.msg("Сумма должна быть числом."); return
        con=db(); r=con.execute("SELECT id FROM users WHERE username=?",(u,)).fetchone()
        if r: con.execute("UPDATE users SET balance=balance+? WHERE id=?",(n,r[0])); con.commit()
        con.close(); lay._popup.dismiss(); self.msg("Валюта выдана." if r else "Игрок не найден.")

class OSINTWorld(App):
    def build(self):
        Window.clearcolor=BG
        init_db()
        self.uid=None; self.username=""
        sm=ScreenManager()
        for name,cls in [("login",Login),("register",Register),("home",Home),("profile",Profile),("chat",Chat),
                         ("tasks",Tasks),("market",Market),("anon",Anon),("files",Files),("search",Terminal),
                         ("takedown",Terminal),("admin",Admin)]:
            s=cls(name=name)
            if name=="takedown": s.mode="takedown"
            sm.add_widget(s)
        self.sm=sm
        Clock.schedule_once(lambda *_: self.start_tasks(), .5)
        return sm
    def start_tasks(self):
        make_task()
        Clock.schedule_interval(lambda *_: make_task(),30)

if __name__=="__main__":
    OSINTWorld().run()
