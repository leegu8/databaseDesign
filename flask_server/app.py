from flask import Flask, request, jsonify, redirect, url_for, send_from_directory, render_template, session, url_for, make_response
from flask_mysqldb import MySQL
import MySQLdb
from datetime import datetime
import os
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
import requests
import calendar
from deep_translator import GoogleTranslator
import openai
from html import unescape
import json
import ast

app = Flask(__name__)
app.secret_key = os.urandom(24)  # 24바이트 랜덤 키 
BASE_DIR = os.path.dirname(__file__)  # /flask_server
STATIC_FOLDER = os.path.join(BASE_DIR, 'static_image')  # /flask_server/static
HTML_FOLDER = os.path.join(BASE_DIR, 'html')  # /flask_server/html

# Ensure static folder exists
os.makedirs(STATIC_FOLDER, exist_ok=True)
app.config['STATIC_FOLDER'] = STATIC_FOLDER

# .env 파일에서 환경 변수 로드
load_dotenv()

# OpenAI API 설정
STABILITY_API_KEY = os.getenv("API_KEY")
# MySQL 설정
app.config['MYSQL_HOST'] = os.getenv("MYSQL_HOST")
app.config['MYSQL_USER'] = os.getenv("MYSQL_USER")
app.config['MYSQL_PASSWORD'] = os.getenv("MYSQL_PASSWORD")
app.config['MYSQL_DB'] = os.getenv("MYSQL_DB")

mysql = MySQL(app)

# Stability API URL
STABILITY_API_URL = "https://api.stability.ai/v2beta/stable-image/generate/core"


# 정적 파일 경로 설정
@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('css', filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('js', filename)

@app.route('/img/<path:filename>')
def serve_img(filename):
    return send_from_directory('img', filename)

# 정적 파일 경로 등록
@app.route('/static_image/<path:filename>')
def serve_static_image(filename):
    return send_from_directory('static_image', filename)

# 정적 파일 경로 등록
@app.route('/<userName>/<path:filename>')
def serve_my_image(userName, filename):
    directory = f'{userName}'
    return send_from_directory(directory, filename)

@app.route('/myCalendar')
def my_calendar():
    return render_template('myCalendar.html')

@app.route('/shareCalendar')
def share_calendar():
    return render_template('shareCalendar.html')

@app.route('/createDream')
def go_create_dream():
    return render_template('createDream.html')

@app.route('/')
def serve_index():
    error = request.args.get('error', None)
    success = request.args.get('success', None)

    # userName, error, success를 템플릿에 전달
    return render_template('index.html', error=error, success=success)


@app.route('/signin', methods=['POST'])
def signin():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        userId = data.get('userId')
        password = data.get('password')
        userName = data.get('userName')

        if not userId or not password or not userName:
            return jsonify({"error": "작성하지 않은 칸이 있습니다!"}), 400

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        check_query = """
        SELECT * FROM accounts
        WHERE userId = %s OR userName = %s OR password = %s
        """
        cursor.execute(check_query, (userId, userName, password))
        result = cursor.fetchone()

        if result:
            cursor.close()
            return jsonify({"error": "중복된 ID, PASSWORD, NAME이 존재합니다!"}), 400

        insert_query = "INSERT INTO accounts (userId, password, userName) VALUES (%s, %s, %s)"
        cursor.execute(insert_query, (userId, password, userName))
        mysql.connection.commit()

        table_name = f"myDreamDiary_{userName}"
        create_table_query = f"""
        CREATE TABLE {table_name} (
            date DATE PRIMARY KEY NOT NULL,
            imgPath VARCHAR(255) NOT NULL,
            dreamCharacter TEXT,
            time ENUM('아침', '점심', '저녁', '새벽') NOT NULL,
            background VARCHAR(255),
            mood VARCHAR(255),
            color VARCHAR(255),
            act VARCHAR(255)
        )
        """
        cursor.execute(create_table_query)
        mysql.connection.commit()
        cursor.close()

        return jsonify({"success": "회원가입이 성공적으로 완료되었습니다!"}), 201
    except MySQLdb.Error as e:
        return jsonify({"error": str(e)}), 500



@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        userId = data.get('userId')
        password = data.get('password')

        if not userId or not password:
            return jsonify({"error": "작성하지 않은 칸이 있습니다!"}), 400

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query = "SELECT userName FROM accounts WHERE userId = %s AND password = %s"
        cursor.execute(query, (userId, password))
        result = cursor.fetchone()
        cursor.close()

        if result:
            userName = result['userName']
            response = jsonify({"success": f"로그인이 성공적으로 완료되었습니다! 어서오세요 {userName}님!"})
            response.set_cookie('userName', userName, httponly=False)
            return response
        else:
            return jsonify({"error": "Invalid userId or password"}), 400
    except MySQLdb.Error as e:
        return jsonify({"error": str(e)}), 500

    
@app.route('/logout', methods=['POST'])
def logout():
    try:
        response = make_response(redirect(url_for('serve_index')))
        response.delete_cookie('userName')  # 쿠키 삭제
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/dreamDraw/result/<userName>/<year>/<month>/<day>', methods=['POST'])
def create_dream(userName, year, month, day):
    try:
        print("===== POST 요청 수신 =====")
        # 쿠키에서 userName 가져오기
        userName = request.cookies.get('userName')
        if not userName:
            return jsonify({"error": "No userName in cookies"}), 400
        print(f"userName: {userName}, year: {year}, month: {month}, day: {day}")

        # 요청 데이터 가져오기
        data = request.json
        print("받은 데이터:", data)

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # JSON 데이터 추출
        dreamCharacter = ", ".join(data.get("character", []))
        time = data.get("time", "")
        background = data.get("background", "")
        mood = data.get("mood", "")
        color = data.get("color", "")
        act = data.get("act", "")
        date = data.get("date", "")

        print("추출된 데이터:")
        print(f"dreamCharacter: {dreamCharacter}, time: {time}, background: {background}")
        print(f"mood: {mood}, color: {color}, act: {act}, date: {date}")

        # 프롬프트 생성
        prompt = f"{dreamCharacter}가 {time}에 {background}에서 {act}. 분위기는 {mood}하고, 색감은 {color}야. 등장인물은 한국인이야."
        # 한국어 문장을 영어로 번역
        english_prompt = GoogleTranslator(source='auto', target='en').translate(prompt)
        print("Stable Diffusion 프롬프트:", english_prompt)

        # 요청 헤더 및 데이터 설정
        headers = {
            "Authorization": f"Bearer {STABILITY_API_KEY}",
            "Accept": "image/*",  # 이미지를 기대
        }
        files = {
            "prompt": (None, english_prompt),
            "aspect_ratio": (None, "3:2"),
            "seed": (None, "0"),
            "output_format": (None, "jpeg")
        }

        # Stability AI API 호출
        print("API 요청 파라미터:", files)
        response = requests.post(STABILITY_API_URL, files=files, headers=headers)

        print("API 응답 상태 코드:", response.status_code)
        
        # 응답 상태 코드 확인
        if response.status_code != 200:
            print("API 응답 본문:", response.text)
            return jsonify({"error": response.json()}), response.status_code

        # 이미지 저장
        filename = f"{userName}_{year}{month}{day}.png"
        print(filename)
        filepath = os.path.join(STATIC_FOLDER, filename)
        with open(filepath, "wb") as f:
            f.write(response.content)  # 이미지 바이너리를 파일로 저장

        print(f"이미지 저장 완료: {filepath}")

        # 세션에 데이터 저장
        session_key = f"{userName}_{year}{month}{day}_myDreram"
        session[session_key] = {
            "imgPath": f"/static_image/{filename}",
            "dreamCharacter": dreamCharacter.split(", "),
            "time": time,
            "background": background,
            "mood": mood,
            "color": color,
            "act": act,
            "date": date
        }
        # 세션에서 데이터 가져오기
        dream_data = session.get(session_key)
        print(dream_data)
        # GET 요청으로 리디렉트
        return redirect(url_for('get_dream_result', userName=userName, year=year, month=month, day=day))

    except Exception as e:
        print("예외 발생:", str(e))
        return jsonify({"error": str(e)}), 500
    
@app.route('/dreamDraw/result/<userName>/<year>/<month>/<day>', methods=['GET'])
def get_dream_result(userName, year, month, day):
    try:
        print("===== GET 요청 수신 =====")
        print(f"userName: {userName}, year: {year}, month: {month}, day: {day}")

        # 세션에서 데이터 가져오기
        session_key = f"{userName}_{year}{month}{day}_myDreram"
        dream_data = session.get(session_key)
        if not dream_data:
            print("세션 데이터가 없습니다.")
            return "Session data not found", 404
        
        return render_template(
        'myDreamdraw_result.html',
        userName=userName,
        imgPath=dream_data["imgPath"],  # URL 경로가 이미 준비됨
        dreamCharacter=dream_data["dreamCharacter"],
        time=dream_data["time"],
        background=dream_data["background"],
        mood=dream_data["mood"],
        color=dream_data["color"],
        act=dream_data["act"],
        date=dream_data["date"]
    )
    except Exception as e:
        print(f"오류 발생: {e}")
        return f"오류 발생: {e}", 500




@app.route('/dreamDraw/result/cancel', methods=['POST'])
def cancel():
    try:
        # static 폴더 내 모든 파일 삭제
        for filename in os.listdir(STATIC_FOLDER):
            file_path = os.path.join(STATIC_FOLDER, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print("모든 이미지를 삭제했습니다.")
         # 성공 상태만 반환
        return jsonify({"message": "All images deleted successfully."}), 200
    except Exception as e:
        print(f"오류 발생: {e}")
        return f"오류 발생: {e}", 500
    
@app.route('/result/cancel', methods=['POST'])
def cancel_default():
    try:
        print("홈으로 돌아갑니다.")
         # 성공 상태만 반환
        return jsonify({"message": "All images deleted successfully."}), 200
    except Exception as e:
        print(f"오류 발생: {e}")
        return f"오류 발생: {e}", 500
    

@app.route('/dreamDraw/save/<userName>/<year>/<month>/<day>', methods=['POST'])
def save_dream(userName, year, month, day):
    try:
        # 요청 JSON 데이터 파싱
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        # Raw dreamCharacter 데이터 추출
        raw_dreamCharacter = data.get("dreamCharacter", "[]")  # 기본값을 빈 리스트로 설정
        print(f"Raw dreamCharacter data: {raw_dreamCharacter}")

        # HTML 엔티티 디코딩
        decoded_dreamCharacter = unescape(raw_dreamCharacter)
        print(f"Partially Decoded dreamCharacter: {decoded_dreamCharacter}")

        # 안전하게 문자열을 리스트로 변환
        try:
            dreamCharacter_list = ast.literal_eval(decoded_dreamCharacter)
            if not isinstance(dreamCharacter_list, list):
                raise ValueError("dreamCharacter is not a list")
        except (ValueError, SyntaxError) as e:
            print(f"Error parsing dreamCharacter as list: {e}")
            return jsonify({"error": "Invalid format for dreamCharacter"}), 400

        # 리스트 내 요소를 디코딩
        dreamCharacter = ", ".join([unescape(char) for char in dreamCharacter_list])
        print(f"Final Decoded dreamCharacter: {dreamCharacter}")
        time = data.get("time", "")
        background = data.get("background", "")
        mood = data.get("mood", "")
        color = data.get("color", "")
        act = data.get("act", "")
        date = data.get("date", "")

        # 기존 이미지 경로
        image_name = f"{userName}_{year}{month}{day}.png"
        old_image_path = os.path.join(STATIC_FOLDER, image_name)

        # 유저 디렉토리 경로
        user_folder = os.path.join(BASE_DIR, userName)
        new_image_path = os.path.join(user_folder, image_name)

        # 이미지 파일 이동
        if not os.path.exists(old_image_path):
            return jsonify({"error": "Image not found"}), 404

        try:
            # 유저 폴더가 없으면 생성
            if not os.path.exists(user_folder):
                os.makedirs(user_folder)
                print(f"User folder created: {user_folder}")

            # 이미지 파일 이동 (덮어쓰기 포함)
            if os.path.exists(new_image_path):
                print(f"File already exists. Overwriting: {new_image_path}")
            os.replace(old_image_path, new_image_path)  # 기존 파일 덮어쓰기
            print(f"Image moved to {new_image_path}")
        except OSError as e:
            print(f"Error occurred while moving the file: {e}")
            return jsonify({"error": f"File operation failed: {e}"}), 500
        
        # 새로운 값 삽입
        imgPath = f"/{userName}/{userName}_{year}{month}{day}.png"

        # 데이터베이스 처리
        table_name = f"mydreamdiary_{userName}"
        cursor = mysql.connection.cursor()

        # 기존 값 삭제 (있으면 삭제, 없으면 무시)
        delete_query = f"DELETE FROM {table_name} WHERE date = %s"
        cursor.execute(delete_query, (date,))
        print(f"Existing entry for date {date} deleted (if existed).")
        # 새로운 값 삽입
        insert_query = f"""
        INSERT INTO {table_name} (date, imgPath, dreamCharacter, time, background, mood, color, act)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (date, imgPath, dreamCharacter, time, background, mood, color, act))
        mysql.connection.commit()
        cursor.close()
        # static 폴더 내 모든 파일 삭제
        for filename in os.listdir(STATIC_FOLDER):
            file_path = os.path.join(STATIC_FOLDER, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print("모든 이미지를 삭제했습니다.")
        
         # 성공 상태만 반환
        return jsonify({"message": "All images saved successfully."}), 200
    except MySQLdb.Error as e:
        print(f"MySQL Error: {e}")
        return jsonify({"error": str(e)}), 500

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500



@app.route('/myCalendar/<year>/<month>', methods=['GET'])
def get_monthly_calendar(year, month):
    try:
        # 입력값 처리
        year = int(year)
        month = int(month)
         # 쿠키에서 userName 가져오기
        userName = request.cookies.get('userName')
        if not userName:
            return jsonify({"error": "User is not logged in"}), 401
        table_name = f"mydreamdiary_{userName}"  # 유저별 테이블

        # 해당 월의 일 수 가져오기
        _, num_days = calendar.monthrange(year, month)

        # DB 연결 및 조회
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query = f"""
        SELECT date, color FROM {table_name}
        WHERE YEAR(date) = %s AND MONTH(date) = %s
        """
        cursor.execute(query, (year, month))
        db_results = cursor.fetchall()  # DB 결과 가져오기
        cursor.close()

        # DB 결과를 딕셔너리로 변환 {날짜: 색상값}
        db_data = {result['date'].strftime('%Y-%m-%d'): result['color'] for result in db_results}

        # 응답 데이터 생성
        calendar_data = []
        for day in range(1, num_days + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            if date_str in db_data:
                calendar_data.append({
                    "year": str(year),
                    "month": f"{month:02d}",
                    "day": f"{day:02d}",
                    "dateState": True,
                    "dateColor": db_data[date_str]
                })
            else:
                calendar_data.append({
                    "year": str(year),
                    "month": f"{month:02d}",
                    "day": f"{day:02d}",
                    "dateState": False,
                    "dateColor": None
                })

        # 데이터를 HTML에 전달하여 렌더링
        return render_template('/myCalendar.html', userName=userName, calendarData=calendar_data)

    except MySQLdb.Error as e:
        print(f"MySQL Error: {e}")
        return jsonify({"error": str(e)}), 500

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500



@app.route('/myCalendar/view/<year>/<month>/<day>', methods=['POST'])
def set_daily_dream(year, month, day):
    try:
        # 쿠키에서 userName 가져오기
        userName = request.cookies.get('userName')
        if not userName:
            return redirect('/login')  # 로그인되지 않은 경우 리다이렉트

        # 데이터베이스 조회
        table_name = f"mydreamdiary_{userName}"
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query = f"""
        SELECT date, imgPath, dreamCharacter, time, background, mood, color, act
        FROM {table_name}
        WHERE date = %s
        """
        cursor.execute(query, (f"{year}{month}{day}",))
        result = cursor.fetchone()
        cursor.close()

        # 데이터가 없는 경우 처리
        if not result:
            return render_template(
                'myCalendar_view.html',
                error="해당 날짜의 꿈 데이터가 없습니다."
            )

       # 세션 키를 사용자 및 날짜별로 설정
        session_key_view = f"{userName}_{year}{month}{day}_viewData"
        session[session_key_view] = {
            "imgPath": result["imgPath"],
            "dreamCharacter": result["dreamCharacter"].split(", "),  # 문자열 → 리스트
            "time": result["time"],
            "background": result["background"],
            "mood": result["mood"],
            "color": result["color"],
            "act": result["act"],
            "date": result["date"]  # 이 부분 추가
        }

        # 세션에서 데이터 가져오기
        viewData = session.get(session_key_view)
        print("세션에 저장된 값: ", viewData)

        # GET 요청으로 리디렉션
        return jsonify({"redirect": url_for('get_daily_dream', userName = userName, year=year, month=month, day=day)}), 200

    except Exception as e:
        print(f"Error fetching daily dream: {e}")
        return render_template('myDreamDraw_view.html', error="서버 오류 발생")
    
@app.route('/myCalendar/view/<userName>/<year>/<month>/<day>', methods=['GET'])
def get_daily_dream(userName, year, month, day):
    try:
        # 쿠키에서 userName 가져오기
        userName = request.cookies.get('userName')
        if not userName:
            return redirect('/login')  # 로그인되지 않은 경우 리다이렉트

        # 세션 키 생성
        session_key_view = f"{userName}_{year}{month}{day}_viewData"

        # 세션에서 데이터 가져오기
        viewData = session.get(session_key_view)
        if not viewData:
            return render_template('myCalendar_view.html', error="No data available for this date")

        # 템플릿 렌더링
        return render_template(
            'myCalendar_view.html',
            userName=userName,
            imgPath=viewData["imgPath"],
            dreamCharacter=viewData["dreamCharacter"],
            time=viewData["time"],
            background=viewData["background"],
            mood=viewData["mood"],
            color=viewData["color"],
            act=viewData["act"],
            date=viewData["date"]
        )
    except Exception as e:
        print("GET 처리 오류:", str(e))
        return render_template('myCalendar_view.html', error="Server error occurred")





# 6. 본인 꿈 캘린더 공유 API
@app.route('/myCalendar/share/<userName>/<year>/<month>/<day>', methods=['POST'])
def share_daily_dream(userName, year, month, day):
    try:
        # 요청 JSON 데이터 파싱
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        # Raw dreamCharacter 데이터 추출
        raw_dreamCharacter = data.get("dreamCharacter", "[]")  # 기본값을 빈 리스트로 설정
        print(f"Raw dreamCharacter data: {raw_dreamCharacter}")

        # HTML 엔티티 디코딩
        decoded_dreamCharacter = unescape(raw_dreamCharacter)
        print(f"Partially Decoded dreamCharacter: {decoded_dreamCharacter}")

        # 안전하게 문자열을 리스트로 변환
        try:
            dreamCharacter_list = ast.literal_eval(decoded_dreamCharacter)
            if not isinstance(dreamCharacter_list, list):
                raise ValueError("dreamCharacter is not a list")
        except (ValueError, SyntaxError) as e:
            print(f"Error parsing dreamCharacter as list: {e}")
            return jsonify({"error": "Invalid format for dreamCharacter"}), 400

        # 리스트 내 요소를 디코딩
        dreamCharacter = ", ".join([unescape(char) for char in dreamCharacter_list])
        print(f"Final Decoded dreamCharacter: {dreamCharacter}")
        imgPath = data.get("imgPath", "")
        print(imgPath)
        time = data.get("time", "")
        background = data.get("background", "")
        mood = data.get("mood", "")
        color = data.get("color", "")
        act = data.get("act", "")
        raw_date = data.get("date", "")  # 'Tue, 03 Dec 2024 00:00:00 GMT'

        # Convert raw_date to 'YYYY-MM-DD' format
        try:
            parsed_date = datetime.strptime(raw_date, "%a, %d %b %Y %H:%M:%S %Z")  # Parse the string
            formatted_date = parsed_date.strftime("%Y-%m-%d")  # Format as 'YYYY-MM-DD'
            print(formatted_date)
        except ValueError as e:
            return jsonify({"error": f"Invalid date format: {raw_date}"}), 400

        # 데이터베이스 처리
        table_name = "shareddreamdiary"
        cursor = mysql.connection.cursor()

        # 기존 값 삭제
        delete_query = f"DELETE FROM {table_name} WHERE userName = %s AND date = %s"
        cursor.execute(delete_query, (userName, formatted_date))
        print(f"Existing entry for userName {userName}, date {formatted_date} deleted (if existed).")

        # 새로운 값 삽입
        insert_query = f"""
        INSERT INTO {table_name} (userName, date, imgPath, dreamCharacter, time, background, mood, color, act)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (userName, formatted_date, imgPath, dreamCharacter, time, background, mood, color, act))
        mysql.connection.commit()
        cursor.close()
        
         # 성공 상태만 반환
        return jsonify({"message": "All images saved successfully."}), 200
    except MySQLdb.Error as e:
        print(f"MySQL Error: {e}")
        return jsonify({"error": str(e)}), 500

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

# 공유 캘린더 조회 API
@app.route('/shareCalendar/<year>/<month>/<day>', methods=['GET'])
def get_shared_calendar(year, month, day):
    try:
        # 데이터베이스에서 해당 날짜에 대한 공유된 데이터를 조회
        table_name = "shareddreamdiary"
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query = f"""
        SELECT userName, color
        FROM {table_name}
        WHERE date = %s
        """
        # 날짜 필드를 'YYYY-MM-DD' 형식으로 전달
        formatted_date = f"{year}-{month}-{day}"
        cursor.execute(query, (formatted_date,))
        results = cursor.fetchall()
        cursor.close()

        # 공유된 데이터가 없는 경우 빈 배열 반환
        if not results:
            return jsonify({"clouds": []}), 200

        # 결과 데이터 가공
        clouds = [{"userName": result["userName"], "color": result["color"]} for result in results]

        # 응답 반환
        return jsonify({"clouds": clouds}), 200
    except MySQLdb.Error as e:
        print(f"MySQL Error: {e}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
    
    
@app.route('/shareCalendar/view/<userName>/<year>/<month>/<day>', methods=['POST'])
def set_shared_dream(userName, year, month, day):
    try:
        # 데이터베이스 조회
        table_name = "shareddreamdiary"
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # 날짜 형식을 'YYYY-MM-DD'로 조합
        formatted_date = f"{year}-{month}-{day}"

        # 데이터베이스에서 조회
        query = f"""
        SELECT userName, imgPath, dreamCharacter, time, background, mood, color, act, date
        FROM {table_name}
        WHERE userName = %s AND date = %s
        """
        cursor.execute(query, (userName, formatted_date))
        result = cursor.fetchone()
        cursor.close()

        # 데이터가 없는 경우 처리
        if not result:
            print(f"No data found for user: {userName}, date: {formatted_date}")
            return jsonify({"error": "No data found for the specified user and date"}), 404

        # 세션 키 생성
        session_key_view = f"{userName}_{year}{month}{day}_sharedViewData"
        session[session_key_view] = {
            "imgPath": result["imgPath"],
            "dreamCharacter": result["dreamCharacter"].split(", "),  # 문자열 → 리스트
            "time": result["time"],
            "background": result["background"],
            "mood": result["mood"],
            "color": result["color"],
            "act": result["act"],
            "date": formatted_date
        }

        # 세션 데이터 확인
        print("세션 저장된 데이터:", session[session_key_view])

        # 리디렉션 URL 반환
        return jsonify({"redirect": url_for('get_shared_dream', userName=userName, year=year, month=month, day=day)}), 200

    except Exception as e:
        print(f"Error fetching shared dream: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/shareCalendar/view/<userName>/<year>/<month>/<day>', methods=['GET'])
def get_shared_dream(userName, year, month, day):
    try:
        # 세션 키 생성
        session_key_view = f"{userName}_{year}{month}{day}_sharedViewData"

        # 세션에서 데이터 가져오기
        viewData = session.get(session_key_view)
        if not viewData:
            print("No session data found")
            return render_template('shareDreamDraw_view.html', error="No data available for this date")

        # 템플릿 렌더링
        return render_template(
            'shareDreamDraw_view.html',
            userName=userName,
            imgPath=viewData["imgPath"],
            dreamCharacter=viewData["dreamCharacter"],
            time=viewData["time"],
            background=viewData["background"],
            mood=viewData["mood"],
            color=viewData["color"],
            act=viewData["act"],
            date=viewData["date"]
        )
    except Exception as e:
        print("GET 처리 오류:", str(e))
        return render_template('shareDreamDraw_view.html', error="Server error occurred")





if __name__ == '__main__':
    app.run(debug=True, port=5000)
