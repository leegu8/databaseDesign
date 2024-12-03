document.addEventListener("DOMContentLoaded", () => {
    const profileIcon = document.getElementById("profileIcon");
    const profileMenu = document.getElementById("profileMenu");
    const loginButton = document.getElementById("loginButton");
    const signInButton = document.getElementById("signInButton");
    const logoutButton = document.getElementById("logoutButton");
    const userNameDisplay = document.getElementById("userNameDisplay");
    const authMenu = document.getElementById("authMenu");
    const userMenu = document.getElementById("userMenu");
    const popup = document.getElementById("popup");
    const popupMessage = document.getElementById("popupMessage");
    const popupCloseButton = document.getElementById("popupCloseButton");
    const navLinks = document.querySelectorAll(".nav-link");

    let loggedInUser = null; // 사용자 상태 관리

    function showPopup(message) {
        popupMessage.textContent = message;
        popup.classList.remove("hidden");
    }

    function closePopup() {
        popup.classList.add("hidden");
    }

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



    // 네비게이션 제한
    navLinks.forEach(link => {
        link.addEventListener("click", (e) => {
            const userName = getCookieValue("userName"); // 쿠키에서 userName 확인
            if (link.dataset.requiresLogin === "true" && !userName) {
                e.preventDefault(); // 링크 이동 방지
                showPopup("로그인이 필요합니다."); // 팝업 표시
            }
        });
    });

    // UI 업데이트
    function updateUI() {
        if (loggedInUser) {
            authMenu.classList.add("hidden");
            userMenu.classList.remove("hidden");
            userNameDisplay.textContent = `안녕하세요, ${loggedInUser.username}`;
        } else {
            authMenu.classList.remove("hidden");
            userMenu.classList.add("hidden");
        }
    }

    // 팝업 닫기
    popupCloseButton.addEventListener("click", closePopup);

    // 초기 UI 설정
    updateUI();
});
