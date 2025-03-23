from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_mysqldb import MySQL
import bcrypt
from db import mysql, init_db
from dotenv import load_dotenv
import os

# 환경 변수 로드
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # .env에서 비밀 키 가져오기

# DB 설정 내용 호출
init_db(app)

# 홈
@app.route('/')
def home():
    return render_template('index.html')

# 회원가입
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        id = request.form['id']
        password = request.form['password'].encode('utf-8')
        name = request.form['name']
        school = request.form['school']
        birthdate = request.form['birthdate']
        
        # 비밀번호 해싱
        hashed_pw = bcrypt.hashpw(password, bcrypt.gensalt())
        
        # DB에 데이터 삽입
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO student (id, password, name, school, birthdate) VALUES (%s, %s, %s, %s, %s)",
                    (id, hashed_pw, name, school, birthdate))
        mysql.connection.commit()
        cur.close()
        
        flash('회원가입되었습니다.')
        return redirect('/login')
    
    return render_template('register.html')

# 로그인
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        id = request.form['id']
        password = request.form['password'].encode('utf-8')
        
        # DB에서 사용자 정보 가져오기
        cur = mysql.connection.cursor()
        cur.execute("SELECT password FROM student WHERE id = %s", (id,))
        user = cur.fetchone()
        cur.close()
        
        if user and bcrypt.checkpw(password, user[0].encode('utf-8')):
            session['user_id'] = id  # 세션 저장
            flash('로그인 성공')
            return redirect('/')
        else:
            flash('로그인 실패. 아이디나 비밀번호를 확인해주세요.')  # 경고 메시지 추가
            return redirect('/login')  # 로그인 페이지로 리디렉션
    
    return render_template('login.html')

# 로그아웃
@app.route('/logout')
def logout():
    if 'user_id' not in session:  # 로그인하지 않은 사용자라면 로그아웃 불가
        return redirect('/login')  # 로그인 페이지로 리디렉션
    
    session.pop('user_id', None)  # 세션에서 user_id 제거
    flash('로그아웃되었습니다.')
    return redirect('/login')  # 로그인 페이지로 리디렉션


# 게시판 목록
@app.route('/board')
def board():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM board ORDER BY created_at DESC")
    posts = cur.fetchall()
    cur.close()
    return render_template('board.html', posts=posts)

# 게시글 작성
@app.route('/board/create', methods=['GET', 'POST'])
def create_post():
    if 'user_id' not in session:  # 로그인되지 않은 사용자는 작성할 수 없음
        return redirect('/login')
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        user_id = session['user_id']  # 로그인한 사용자의 ID를 가져옴

        cur = mysql.connection.cursor()
        # 게시글을 작성하면서 user_id도 함께 저장
        cur.execute("INSERT INTO board (title, content, user_id) VALUES (%s, %s, %s)",
                    (title, content, user_id))
        mysql.connection.commit()
        cur.close()

        return redirect('/board')  # 게시판 목록으로 리디렉션
    
    return render_template('create_post.html')

# 게시글 읽기 (상세보기)
@app.route('/board/read/<int:post_id>')
def read_post(post_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM board WHERE no = %s", (post_id,))
    post = cur.fetchone()
    cur.close()

    if post:
        return render_template('read_post.html', post=post)
    else:
        return redirect('/board')

# 게시글 수정
@app.route('/board/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM board WHERE no = %s", (post_id,))
    post = cur.fetchone()
    
    if not post or post[3] != session['user_id']:  # 작성자 본인이 아닌 경우
        flash('이 게시글은 수정할 수 없습니다.')
        return redirect('/board')
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        cur.execute("UPDATE board SET title = %s, content = %s, updated_at = CURRENT_TIMESTAMP WHERE no = %s",
                    (title, content, post_id))
        mysql.connection.commit()
        cur.close()
        
        return redirect('/board')
    
    cur.close()
    return render_template('edit_post.html', post=post)

# 게시글 삭제
@app.route('/board/delete/<int:post_id>')
def delete_post(post_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM board WHERE no = %s", (post_id,))
    post = cur.fetchone()
    
    if not post or post[3] != session['user_id']:  # 작성자 본인이 아닌 경우
        flash('이 게시글은 삭제할 수 없습니다.')
        return redirect('/board')
    
    cur.execute("DELETE FROM board WHERE no = %s", (post_id,))
    mysql.connection.commit()
    cur.close()
    
    return redirect('/board')


@app.route('/board/search')
def search_board():
    query = request.args.get('query', '').strip()
    filter_type = request.args.get('filter', 'all')

    if not query:
        return redirect('/board')  # 검색어가 없으면 게시판으로 리디렉트

    cur = mysql.connection.cursor()

    # 검색 조건 설정
    if filter_type == 'title':
        cur.execute("SELECT * FROM board WHERE title LIKE %s ORDER BY created_at DESC", ('%' + query + '%',))
    elif filter_type == 'content':
        cur.execute("SELECT * FROM board WHERE content LIKE %s ORDER BY created_at DESC", ('%' + query + '%',))
    else:  # 'all' (제목 + 내용 검색)
        cur.execute("SELECT * FROM board WHERE title LIKE %s OR content LIKE %s ORDER BY created_at DESC", 
                    ('%' + query + '%', '%' + query + '%'))

    search_results = cur.fetchall()
    cur.close()

    return render_template('search_results.html', posts=search_results, query=query)

if __name__ == '__main__':
    app.run(debug=True)