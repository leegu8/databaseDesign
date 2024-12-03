document.addEventListener("DOMContentLoaded", () => {
  const menuButton = document.getElementById("menuButton");
  const menuItems = document.getElementById("menuItems");
  const profileIcon = document.getElementById("profileIcon");
  const profileMenu = document.getElementById("profileMenu");
  const dreamMenu = document.getElementById("dreamMenu");
  const nextButton = document.getElementById("nextButton");
  const prevButton = document.getElementById("prevButton");
  const submitButton = document.querySelector('button[type="submit"]');
  const bufferingScreen = document.getElementById("bufferingScreen"); // 버퍼링 화면 요소
  const addCharacterButton = document.getElementById("addCharacterButton");
  const characterInputs = document.getElementById("characterInputs");


  // 유저 이름 변수
  let userName = null;

  // 왼쪽 메뉴 버튼 클릭 시
  menuButton.addEventListener("click", () => {
    menuItems.classList.toggle("hidden");
  });
// 쿠키에서 userName 값 읽기
function getCookieValue(cookieName) {
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === cookieName) {
          return decodeURIComponent(value);
      }
  }
  return null;
}

// 오른쪽 프로필 메뉴 클릭 시
profileIcon.addEventListener("click", () => {
  profileMenu.classList.toggle("hidden");

  const authMenu = document.getElementById("authMenu");
  const userMenu = document.getElementById("userMenu");
  const userNameDisplay = document.getElementById("userNameDisplay");

  const userName = getCookieValue("userName");

  if (userName === null) {
      authMenu.classList.remove("hidden");
      userMenu.classList.add("hidden");
  } else {
      authMenu.classList.add("hidden");
      userMenu.classList.remove("hidden");
      userNameDisplay.textContent = `어서오세요, ${userName}님!`;
  }
});

// 회원가입
signInButton.addEventListener("click", async () => {
  const userId = prompt("아이디를 입력하세요:");
  const password = prompt("비밀번호를 입력하세요:");
  const userName = prompt("닉네임을 입력하세요:");

  if (userId && password && userName) {
      const payload = { userId, password, userName };
      try {
          const response = await fetch('/signin', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(payload)
          });

          const data = await response.json();
          if (response.ok) {
              console.log("회원가입 성공:", data.success);
              alert(data.success);
          } else {
              console.error("회원가입 실패:", data.error);
              alert(data.error);
          }
      } catch (error) {
          console.error("Error during sign-up:", error);
      }
  } else {
      console.error("모든 필드를 입력해주세요.");
  }
});

// 로그인
loginButton.addEventListener("click", async () => {
  const userId = prompt("아이디를 입력하세요:");
  const password = prompt("비밀번호를 입력하세요:");

  if (userId && password) {
      const payload = { userId, password };
      try {
          const response = await fetch('/login', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(payload)
          });

          const data = await response.json();
          if (response.ok) {
              console.log("로그인 성공:", data.success);
              alert(data.success);

              // 프로필 메뉴 업데이트
              profileMenu.classList.remove("hidden");
              const userName = getCookieValue("userName");
              const userMenu = document.getElementById("userMenu");
              const authMenu = document.getElementById("authMenu");
              const userNameDisplay = document.getElementById("userNameDisplay");

              if (userName) {
                  authMenu.classList.add("hidden");
                  userMenu.classList.remove("hidden");
                  userNameDisplay.textContent = `어서오세요, ${userName}님!`;
              }
          } else {
              console.error("로그인 실패:", data.error);
              alert(data.error);
          }
      } catch (error) {
          console.error("Error during login:", error);
      }
  } else {
      console.error("아이디와 비밀번호를 입력해주세요.");
  }
});

// 로그아웃
logoutButton.addEventListener("click", async () => {
  try {
      const response = await fetch('/logout', {
          method: 'POST'
      });

      if (response.redirected) {
          alert("로그아웃 되었습니다.");
          window.location.href = response.url; // 성공 시 index.html로 이동
      } else {
          alert("로그아웃에 실패했습니다.");
      }
  } catch (error) {
      console.error("Error during logout:", error);
      alert("로그아웃 중 문제가 발생했습니다.");
  }
});

  // 드림 메뉴 클릭 시 팝업
  dreamMenu.addEventListener("click", () => {
    const keywordPopup = document.getElementById("keywordPopup");
    keywordPopup.classList.remove("hidden");
    setTimeout(() => {
      keywordPopup.classList.add("hidden");
    }, 2000); // 2초 후 팝업 숨김
  });

  // 질문 순서 관리
  const questions = document.querySelectorAll(".question");
  let currentIndex = 0;

  addCharacterButton.addEventListener("click", () => {
    const inputGroup = document.createElement("div");
    inputGroup.classList.add("input-group");
    const input = document.createElement("input");
    input.type = "text";
    input.placeholder = "등장인물 입력";
    inputGroup.appendChild(input);
    characterInputs.appendChild(inputGroup);
});

// 질문 2: 시간 선택 버튼 클릭 시 활성화 상태 추가
const timeButtons = document.querySelectorAll(".time-button");
timeButtons.forEach((button) => {
    button.addEventListener("click", () => {
        timeButtons.forEach((btn) => btn.classList.remove("active"));
        button.classList.add("active");
    });
});

// 질문 5: 분위기 선택 버튼 클릭 시 활성화 상태 추가
const moodButtons = document.querySelectorAll(".mood-button");
moodButtons.forEach((button) => {
    button.addEventListener("click", () => {
        moodButtons.forEach((btn) => btn.classList.remove("active"));
        button.classList.add("active");
    });
});

// 질문 6: 색상 선택 클릭 시 활성화 상태 추가
const colors = document.querySelectorAll(".color");
colors.forEach((color) => {
    color.addEventListener("click", () => {
        colors.forEach((c) => c.classList.remove("active"));
        color.classList.add("active");
    });
});


  function updateQuestionView() {
    questions.forEach((question, index) => {
      question.classList.toggle("hidden", index !== currentIndex);
    });

    prevButton.disabled = currentIndex === 0;

    // 색상 선택 화면에서 "다음" 버튼 제거 및 "꿈 생성" 버튼 활성화
    if (currentIndex === questions.length - 1) {
      nextButton.classList.add("hidden");
      submitButton.disabled = false; // 활성화
      submitButton.classList.remove("disabled");
    } else {
      nextButton.classList.remove("hidden");
      submitButton.disabled = true; // 비활성화
    }
  }

  if (prevButton && nextButton) {
    prevButton.addEventListener("click", () => {
      if (currentIndex > 0) {
        currentIndex--;
        updateQuestionView();
      }
    });

    nextButton.addEventListener("click", () => {
      if (currentIndex < questions.length - 1) {
        currentIndex++;
        updateQuestionView();
      }
    });

    updateQuestionView();
  }

  // 꿈 생성 버튼 클릭 시
  submitButton.addEventListener("click", async (event) => {
    event.preventDefault(); // 기본 동작 중단

    // 버퍼링 화면 표시
    bufferingScreen.classList.remove("hidden");

    // 폼 데이터 수집
    try {
      const userName = "testuser";
      const character = Array.from(
        document.querySelectorAll("#characterInputs input")
      )
        .map((input) => input.value.trim())
        .filter((value) => value);
      const time = document.querySelector(".time-button.active")?.dataset.time;
      const background = document.getElementById("background").value.trim();
      const mood = document.querySelector(".mood-button.active")?.dataset.mood;
      console.log(mood);
      const color = document.querySelector(".color.active")?.dataset.color;
      const act = document.getElementById("act").value.trim();
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0'); // 월은 0부터 시작하므로 +1 필요
      const day = String(now.getDate()).padStart(2, '0');
      
      const date = `${year}${month}${day}`;

      const payload = { character, time, background, mood, color, act, date };

      // 서버 요청
      const url = `/dreamDraw/result/${userName}/${year}/${month}/${day}`;
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        window.location.href = response.url;
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.error}`);
      }
    } catch (error) {
      console.error("Error:", error);
      alert("Error occurred while generating the dream.");
    } finally {
      // 버퍼링 화면 숨김
      bufferingScreen.classList.add("hidden");
    }
  });

  
});
