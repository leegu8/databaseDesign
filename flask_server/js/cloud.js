async function fetchCloudData() {
    console.log("fetchCloudData called");
    try {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, "0");
        const day = String(today.getDate()).padStart(2, "0");

        console.log(`Fetching data for date: ${year}-${month}-${day}`);
        const response = await fetch(`/shareCalendar/${year}/${month}/${day}`);
        console.log("Response status:", response.status);

        if (!response.ok) throw new Error("Failed to fetch data");

        const data = await response.json();
        console.log("Fetched data:", data);

        const { clouds } = data;
        const cloudContainer = document.getElementById("cloudContainer");
        cloudContainer.innerHTML = "";

        clouds.forEach(({ color, userName }) => {
            const colorName = convertColorToName(color);
            const cloudPath = `/img/${colorName}Cloud.svg`;

            // 데이터에 'date'가 없는 경우 기본값 설정
            const date = `${year}-${month}-${day}`;

            const cloud = document.createElement("div");
            cloud.classList.add("cloud");

            cloud.innerHTML = `
                <img src="${cloudPath}" alt="${colorName} Cloud">
                <span style="color: ${color}">${userName || "Anonymous"}</span>
            `;

            const xPosition = Math.random() * 80; // 구름의 좌우 위치 랜덤
            const yPosition = Math.random() * 80; // 구름의 상하 위치 랜덤
            cloud.style.left = `${xPosition}%`;
            cloud.style.top = `${yPosition}%`;

            // 클릭 이벤트 속성 추가
            cloud.setAttribute("data-userName", userName);
            cloud.setAttribute("data-date", date);

            cloudContainer.appendChild(cloud);
        });
    } catch (error) {
        console.error("Error fetching cloud data:", error);
    }
}

function convertColorToName(color) {
    const colorMap = {
        "#FF0000": "red",
        "#FFA500": "orange",
        "#FFFF00": "yellow",
        "#008000": "green",
        "#87CEEB": "skyblue",
        "#0000FF": "blue",
        "#800080": "purple",
        "#FFC0CB": "pink",
        "#000000": "black",
    };
    return colorMap[color.toUpperCase()] || "default";
}

document.addEventListener("DOMContentLoaded", () => {
    console.log("DOMContentLoaded triggered");
    fetchCloudData();

    const cloudContainer = document.getElementById("cloudContainer");

    // 구름 클릭 이벤트 추가
    cloudContainer.addEventListener("click", async (event) => {
        const cloud = event.target.closest(".cloud"); // 클릭한 구름 찾기
        if (!cloud) return; // 구름 외부 클릭 시 무시

        const userName = cloud.getAttribute("data-userName");
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, "0");
        const day = String(today.getDate()).padStart(2, "0");

        console.log(`클릭된 구름 - 사용자: ${userName}, 날짜: ${year}-${month}-${day}`);

        try {
            // POST 요청 전송
            const response = await fetch(`/shareCalendar/view/${userName}/${year}/${month}/${day}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
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
    });
});
