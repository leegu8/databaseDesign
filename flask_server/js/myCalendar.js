document.addEventListener("DOMContentLoaded", () => {
    const circles = document.querySelectorAll(".circle");

    circles.forEach((circle) => {
        circle.addEventListener("click", async () => {
            const day = circle.getAttribute("data-day");
            const month = circle.getAttribute("data-month");
            const year = circle.getAttribute("data-year");
            const state = circle.getAttribute("data-state");

            if (state === "true") {
                console.log(`POST 요청: /myCalendar/view/${year}/${month}/${day}`);

                try {
                    // POST 요청 전송
                    const response = await fetch(`/myCalendar/view/${year}/${month}/${day}`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            imgPath: circle.getAttribute("data-imgPath"),
                            dreamCharacter: circle.getAttribute("data-dreamCharacter"),
                            time: circle.getAttribute("data-time"),
                            background: circle.getAttribute("data-background"),
                            mood: circle.getAttribute("data-mood"),
                            color: circle.getAttribute("data-color"),
                            act: circle.getAttribute("data-act"),
                        }),
                    });

                    if (!response.ok) {
                        throw new Error(`서버 응답 오류: ${response.statusText}`);
                    }

                    // 응답 데이터 처리
                    const result = await response.json();
                    if (result.redirect) {
                        console.log("리디렉션:", result.redirect);
                        window.location.href = result.redirect; // GET 요청으로 리디렉션
                    } else {
                        console.error("리디렉션 URL이 없습니다.");
                        alert("리디렉션에 실패했습니다.");
                    }
                } catch (error) {
                    console.error("POST 요청 실패:", error);
                    alert("서버 호출 중 오류가 발생했습니다.");
                }
            }
        });
    });
});
