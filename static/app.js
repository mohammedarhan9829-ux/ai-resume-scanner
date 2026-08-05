/**
 * Universal AI Resume Scanner & Placement Career Engine
 * Features:
 * 1. AI Bullet Point Rewriter
 * 2. Timed Live Mock Interview Test (10 Questions - 10 Min Limit) with AI Model Answer Comparison & Match %
 * 3. Placement Salary & Market Demand Intelligence
 * 4. ATS Health Compliance Audit (0-100 Score)
 * 5. Full Mobile Touch & Robust Server Build Error Handling
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const dropZone = document.getElementById("dropZone");
    const fileInput = document.getElementById("fileInput");
    const btnBrowse = document.getElementById("btnBrowse");
    const filePreviewBadge = document.getElementById("filePreviewBadge");
    const fileNameText = document.getElementById("fileNameText");
    const fileSizeText = document.getElementById("fileSizeText");
    const fileTypeIcon = document.getElementById("fileTypeIcon");
    const btnRemoveFile = document.getElementById("btnRemoveFile");
    const btnScan = document.getElementById("btnScan");
    const targetJobSelect = document.getElementById("targetJobSelect");
    const loaderContainer = document.getElementById("loaderContainer");
    const loaderText = document.getElementById("loaderText");
    
    const resultsSection = document.getElementById("resultsSection");
    const btnCopyIp = document.getElementById("btnCopyIp");
    const networkIpText = document.getElementById("networkIpText");
    const btnPrintReport = document.getElementById("btnPrintReport");
    const scanLimitBadge = document.getElementById("scanLimitBadge");

    // Feature 1: Bullet Rewriter Elements
    const inputBullet = document.getElementById("inputBullet");
    const btnRewriteBullet = document.getElementById("btnRewriteBullet");
    const rewriteResultsContainer = document.getElementById("rewriteResultsContainer");

    // Interactive Timed 10-Q Mock Test Elements
    const btnStartLiveTest = document.getElementById("btnStartLiveTest");
    const liveTestContainer = document.getElementById("liveTestContainer");
    const testQCounter = document.getElementById("testQCounter");
    const testTimerText = document.getElementById("testTimerText");
    const testCategoryTag = document.getElementById("testCategoryTag");
    const testProgressFill = document.getElementById("testProgressFill");
    const testQText = document.getElementById("testQText");
    const testQHint = document.getElementById("testQHint");
    const testUserAnswer = document.getElementById("testUserAnswer");
    const btnPrevTestQ = document.getElementById("btnPrevTestQ");
    const btnNextTestQ = document.getElementById("btnNextTestQ");
    const btnSubmitTest = document.getElementById("btnSubmitTest");
    const testEvalResultsContainer = document.getElementById("testEvalResultsContainer");

    // Auth & Subscription DOM Elements
    const btnNavAuth = document.getElementById("btnNavAuth");
    const userProfileBadge = document.getElementById("userProfileBadge");
    const userNameNav = document.getElementById("userNameNav");
    const userPlanNav = document.getElementById("userPlanNav");
    const userAvatar = document.getElementById("userAvatar");
    const btnNavUpgrade = document.getElementById("btnNavUpgrade");
    const btnOpenProfile = document.getElementById("btnOpenProfile");

    // Modals
    const authModal = document.getElementById("authModal");
    const btnCloseAuthModal = document.getElementById("btnCloseAuthModal");
    const tabLogin = document.getElementById("tabLogin");
    const tabRegister = document.getElementById("tabRegister");
    const formLogin = document.getElementById("formLogin");
    const formRegister = document.getElementById("formRegister");

    const pricingModal = document.getElementById("pricingModal");
    const btnClosePricingModal = document.getElementById("btnClosePricingModal");
    const btnConfirmUpgrade = document.getElementById("btnConfirmUpgrade");

    const profileModal = document.getElementById("profileModal");
    const btnCloseProfileModal = document.getElementById("btnCloseProfileModal");
    const profileNameLg = document.getElementById("profileNameLg");
    const profileEmailSub = document.getElementById("profileEmailSub");
    const profileAvatarLg = document.getElementById("profileAvatarLg");
    const profilePlanTag = document.getElementById("profilePlanTag");
    const profDailyScans = document.getElementById("profDailyScans");
    const profPlanStatus = document.getElementById("profPlanStatus");
    const historyList = document.getElementById("historyList");
    const btnProfileUpgrade = document.getElementById("btnProfileUpgrade");
    const btnLogout = document.getElementById("btnLogout");

    let selectedFile = null;
    let networkUrl = "";
    let currentUser = null;
    let authToken = localStorage.getItem("user_token") || "";
    let currentScanData = null;

    // Live Test Stepper & Timer State
    let testQuestions = [];
    let currentQIndex = 0;
    let userAnswersMap = {};
    let testTimerInterval = null;
    let secondsRemaining = 600; // 10 Minutes Limit

    // Initial Setup
    fetchNetworkInfo();
    if (authToken) {
        checkAuthStatus();
    } else {
        updateAuthUI(null);
    }

    async function fetchNetworkInfo() {
        try {
            const res = await fetch("/api/network-info");
            if (res.ok) {
                const data = await res.json();
                networkUrl = data.network_url;
                networkIpText.textContent = `LAN IP: ${data.local_ip}:${data.port}`;
            }
        } catch (err) {
            console.warn("Could not fetch network info:", err);
            networkIpText.textContent = "LAN IP: Ready";
        }
    }

    async function checkAuthStatus() {
        try {
            const res = await fetch("/api/auth/me", {
                headers: { "Authorization": `Bearer ${authToken}` }
            });
            if (res.ok) {
                const data = await res.json();
                currentUser = data.user;
                updateAuthUI(currentUser);
            } else {
                localStorage.removeItem("user_token");
                authToken = "";
                updateAuthUI(null);
            }
        } catch (e) {
            updateAuthUI(null);
        }
    }

    function updateAuthUI(user) {
        currentUser = user;
        if (user) {
            btnNavAuth.classList.add("hidden");
            userProfileBadge.classList.remove("hidden");
            userNameNav.textContent = user.name;
            userAvatar.textContent = user.name.charAt(0).toUpperCase();

            if (user.is_pro) {
                userPlanNav.textContent = "PRO 👑";
                userPlanNav.className = "user-plan-tag pro-tag";
                scanLimitBadge.textContent = "Pro Tier: Unlimited Scans 👑";
            } else {
                userPlanNav.textContent = "FREE";
                userPlanNav.className = "user-plan-tag free-tag";
                scanLimitBadge.textContent = `Free Scans: ${user.scans_remaining}/3 Left Today`;
            }
        } else {
            btnNavAuth.classList.remove("hidden");
            userProfileBadge.classList.add("hidden");
            scanLimitBadge.textContent = "Guest Daily Scans: 3/3 Left";
        }
    }

    // Modal Listeners
    btnNavAuth.addEventListener("click", () => authModal.classList.remove("hidden"));
    btnCloseAuthModal.addEventListener("click", () => authModal.classList.add("hidden"));

    btnNavUpgrade.addEventListener("click", () => pricingModal.classList.remove("hidden"));
    btnClosePricingModal.addEventListener("click", () => pricingModal.classList.add("hidden"));

    btnOpenProfile.addEventListener("click", () => openProfileModal());
    btnCloseProfileModal.addEventListener("click", () => profileModal.classList.add("hidden"));
    if (btnProfileUpgrade) {
        btnProfileUpgrade.addEventListener("click", () => {
            profileModal.classList.add("hidden");
            pricingModal.classList.remove("hidden");
        });
    }

    tabLogin.addEventListener("click", () => {
        tabLogin.classList.add("active");
        tabRegister.classList.remove("active");
        formLogin.classList.remove("hidden");
        formRegister.classList.add("hidden");
    });

    tabRegister.addEventListener("click", () => {
        tabRegister.classList.add("active");
        tabLogin.classList.remove("active");
        formRegister.classList.remove("hidden");
        formLogin.classList.add("hidden");
    });

    formLogin.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("loginEmail").value;
        const password = document.getElementById("loginPassword").value;
        try {
            const res = await fetch("/api/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Login failed.");
            authToken = data.token;
            localStorage.setItem("user_token", authToken);
            currentUser = data.user;
            updateAuthUI(currentUser);
            authModal.classList.add("hidden");
            alert(`Welcome back, ${currentUser.name}!`);
        } catch (err) {
            alert(`Login Error: ${err.message}`);
        }
    });

    formRegister.addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = document.getElementById("regName").value;
        const email = document.getElementById("regEmail").value;
        const password = document.getElementById("regPassword").value;
        try {
            const res = await fetch("/api/auth/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, email, password })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Registration failed.");
            authToken = data.token;
            localStorage.setItem("user_token", authToken);
            currentUser = data.user;
            updateAuthUI(currentUser);
            authModal.classList.add("hidden");
            alert(`Account created successfully! Welcome, ${currentUser.name}!`);
        } catch (err) {
            alert(`Registration Error: ${err.message}`);
        }
    });

    btnConfirmUpgrade.addEventListener("click", async () => {
        if (!currentUser) {
            pricingModal.classList.add("hidden");
            authModal.classList.remove("hidden");
            alert("Please log in or create an account first to upgrade to Pro Plan.");
            return;
        }
        try {
            const res = await fetch("/api/subscription/upgrade", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${authToken}`
                },
                body: JSON.stringify({ plan: "pro", payment_ref: "SIMULATED_UPI_SUCCESS_150" })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Upgrade failed.");
            currentUser = data.user;
            updateAuthUI(currentUser);
            pricingModal.classList.add("hidden");
            alert(data.message);
        } catch (err) {
            alert(`Upgrade Error: ${err.message}`);
        }
    });

    btnLogout.addEventListener("click", () => {
        localStorage.removeItem("user_token");
        authToken = "";
        currentUser = null;
        updateAuthUI(null);
        profileModal.classList.add("hidden");
        alert("Logged out successfully.");
    });

    async function openProfileModal() {
        if (!currentUser) return;
        profileNameLg.textContent = currentUser.name;
        profileEmailSub.textContent = currentUser.email;
        profileAvatarLg.textContent = currentUser.name.charAt(0).toUpperCase();

        if (currentUser.is_pro) {
            profilePlanTag.textContent = "PRO SUBSCRIPTION 👑";
            profilePlanTag.className = "user-plan-tag pro-tag";
            profDailyScans.textContent = "Unlimited 👑";
            profPlanStatus.textContent = "Active Pro (₹150/mo)";
        } else {
            profilePlanTag.textContent = "FREE PLAN";
            profilePlanTag.className = "user-plan-tag free-tag";
            profDailyScans.textContent = `${currentUser.scans_remaining}/3 Left`;
            profPlanStatus.textContent = "Free Tier";
        }

        historyList.innerHTML = `<p class="text-muted">Loading scan history...</p>`;
        profileModal.classList.remove("hidden");

        try {
            const res = await fetch("/api/user/history", {
                headers: { "Authorization": `Bearer ${authToken}` }
            });
            if (res.ok) {
                const data = await res.json();
                renderHistory(data.history);
            }
        } catch (e) {
            historyList.innerHTML = `<p class="text-muted">Could not load scan history.</p>`;
        }
    }

    function renderHistory(records) {
        if (!records || records.length === 0) {
            historyList.innerHTML = `<p class="text-muted" style="font-size:0.85rem;">No scan history recorded yet.</p>`;
            return;
        }
        historyList.innerHTML = "";
        records.forEach(item => {
            const dateStr = new Date(item.scanned_at).toLocaleDateString();
            const div = document.createElement("div");
            div.className = "history-item";
            div.innerHTML = `
                <div>
                    <strong>${item.job_title}</strong>
                    <div style="font-size:0.75rem; color:var(--text-muted);">${item.filename} &bull; ${dateStr}</div>
                </div>
                <div style="font-weight:700; color:var(--accent-emerald);">${item.match_percentage}% Match</div>
            `;
            historyList.appendChild(div);
        });
    }

    // FEATURE 1: AI BULLET POINT REWRITER
    btnRewriteBullet.addEventListener("click", async () => {
        const text = inputBullet.value.trim();
        if (!text) {
            alert("Please enter a bullet point to rewrite.");
            return;
        }

        btnRewriteBullet.disabled = true;
        btnRewriteBullet.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Rewriting with AI...`;

        try {
            const res = await fetch("/api/ai/rewrite-bullet", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${authToken}`
                },
                body: JSON.stringify({ original_bullet: text, target_role: targetJobSelect.value || "General Role" })
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Rewrite failed.");

            rewriteResultsContainer.innerHTML = `<strong><i class="fa-solid fa-wand-magic-sparkles text-amber"></i> AI ATS-Optimized Rewrites:</strong>`;
            data.rewritten_bullets.forEach(b => {
                const item = document.createElement("div");
                item.className = "rewrite-item";
                item.textContent = `• ${b}`;
                rewriteResultsContainer.appendChild(item);
            });
            rewriteResultsContainer.classList.remove("hidden");

        } catch (err) {
            alert(`Rewrite Error: ${err.message}`);
        } finally {
            btnRewriteBullet.disabled = false;
            btnRewriteBullet.innerHTML = `<i class="fa-solid fa-bolt text-amber"></i> AI Rewrite Bullet Point`;
        }
    });

    // TIMED LIVE MOCK INTERVIEW TEST LOGIC WITH COUNTDOWN TIMER
    btnStartLiveTest.addEventListener("click", async () => {
        if (!currentScanData) return;
        const jobTitle = currentScanData.target_job_analysis.title;

        btnStartLiveTest.disabled = true;
        btnStartLiveTest.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Generating 10 Questions...`;

        try {
            const res = await fetch("/api/ai/live-interview/questions", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${authToken}`
                },
                body: JSON.stringify({
                    job_title: jobTitle,
                    domain: currentScanData.target_job_analysis.domain
                })
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Failed to generate questions.");

            testQuestions = data.questions;
            currentQIndex = 0;
            userAnswersMap = {};

            liveTestContainer.classList.remove("hidden");
            testEvalResultsContainer.classList.add("hidden");
            
            // Start 10-Minute (600s) Countdown Timer
            startCountdownTimer(600);
            renderTestQuestion(currentQIndex);

        } catch (err) {
            alert(`Test Error: ${err.message}`);
        } finally {
            btnStartLiveTest.disabled = false;
            btnStartLiveTest.innerHTML = `<i class="fa-solid fa-rotate-right"></i> Restart Timed 10-Q Test`;
        }
    });

    function startCountdownTimer(durationSeconds) {
        if (testTimerInterval) clearInterval(testTimerInterval);
        secondsRemaining = durationSeconds;

        updateTimerDisplay();
        testTimerInterval = setInterval(() => {
            secondsRemaining--;
            updateTimerDisplay();

            if (secondsRemaining <= 0) {
                clearInterval(testTimerInterval);
                alert("⏱️ Time's Up! 10-minute interview limit reached. Auto-submitting test for AI Evaluation...");
                submitTestAnswers();
            }
        }, 1000);
    }

    function updateTimerDisplay() {
        const mins = Math.floor(secondsRemaining / 60);
        const secs = secondsRemaining % 60;
        const formatted = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        testTimerText.innerHTML = `<i class="fa-solid fa-stopwatch"></i> ⏱️ ${formatted}`;
        if (secondsRemaining < 120) {
            testTimerText.style.color = "#f43f5e";
        } else {
            testTimerText.style.color = "#e9d5ff";
        }
    }

    function renderTestQuestion(idx) {
        if (idx < 0 || idx >= testQuestions.length) return;

        const q = testQuestions[idx];
        testQCounter.textContent = `Question ${idx + 1} of ${testQuestions.length}`;
        testCategoryTag.textContent = `Category: ${q.category || 'Technical Core'}`;
        testProgressFill.style.width = `${((idx + 1) / testQuestions.length) * 100}%`;

        testQText.textContent = q.question;
        testQHint.textContent = `Hint: ${q.hints || 'Include core technical mechanisms and real-world examples.'}`;
        testUserAnswer.value = userAnswersMap[idx] || "";

        btnPrevTestQ.disabled = (idx === 0);
        if (idx === testQuestions.length - 1) {
            btnNextTestQ.classList.add("hidden");
            btnSubmitTest.classList.remove("hidden");
        } else {
            btnNextTestQ.classList.remove("hidden");
            btnSubmitTest.classList.add("hidden");
        }
    }

    btnPrevTestQ.addEventListener("click", () => {
        userAnswersMap[currentQIndex] = testUserAnswer.value;
        if (currentQIndex > 0) {
            currentQIndex--;
            renderTestQuestion(currentQIndex);
        }
    });

    btnNextTestQ.addEventListener("click", () => {
        userAnswersMap[currentQIndex] = testUserAnswer.value;
        if (currentQIndex < testQuestions.length - 1) {
            currentQIndex++;
            renderTestQuestion(currentQIndex);
        }
    });

    btnSubmitTest.addEventListener("click", () => {
        submitTestAnswers();
    });

    async function submitTestAnswers() {
        if (testTimerInterval) clearInterval(testTimerInterval);

        userAnswersMap[currentQIndex] = testUserAnswer.value;
        const payloadAnswers = testQuestions.map((q, idx) => ({
            question: q.question,
            user_answer: userAnswersMap[idx] || ""
        }));

        btnSubmitTest.disabled = true;
        btnSubmitTest.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Comparing Answers with AI Model...`;

        try {
            const res = await fetch("/api/ai/live-interview/evaluate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${authToken}`
                },
                body: JSON.stringify({
                    job_title: currentScanData.target_job_analysis.title,
                    answers: payloadAnswers
                })
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Evaluation failed.");

            renderEvaluationResults(data);
            liveTestContainer.classList.add("hidden");
            testEvalResultsContainer.classList.remove("hidden");

        } catch (err) {
            alert(`Evaluation Error: ${err.message}`);
        } finally {
            btnSubmitTest.disabled = false;
            btnSubmitTest.innerHTML = `<i class="fa-solid fa-check"></i> Submit Test for AI Evaluation`;
        }
    }

    // Render Side-by-Side Candidate vs Ideal AI Model Answer Evaluation
    function renderEvaluationResults(data) {
        testEvalResultsContainer.innerHTML = `
            <div class="eval-score-banner">
                <span class="eval-score-val">${data.overall_score}%</span>
                <p><strong>Timed Mock Interview Technical Skill Match %</strong></p>
                <p style="font-size:0.82rem; color:var(--text-muted);">Overall match rating comparing your candidate responses against AI Model Answers.</p>
            </div>
            <h4 style="margin-top:1rem;"><i class="fa-solid fa-code-compare text-cyan"></i> Side-by-Side Candidate vs AI Model Answer Breakdown:</h4>
        `;

        data.evaluations.forEach(e => {
            const div = document.createElement("div");
            div.className = "eval-item";
            div.innerHTML = `
                <div class="eval-q-header">
                    <span>Q${e.question_num}: ${e.question}</span>
                    <span style="color:var(--accent-emerald); font-size:0.9rem;">${e.match_percentage}% Answer Match</span>
                </div>
                
                <div style="background:rgba(255,255,255,0.03); border-radius:var(--radius-sm); padding:0.6rem; margin-top:0.3rem;">
                    <strong style="color:var(--text-primary);">Your Candidate Answer:</strong>
                    <p style="color:var(--text-secondary); margin-top:0.25rem;">"${e.user_answer}"</p>
                </div>

                <div style="background:rgba(16,185,129,0.06); border:1px solid rgba(16,185,129,0.3); border-radius:var(--radius-sm); padding:0.6rem; margin-top:0.3rem;">
                    <strong style="color:var(--accent-emerald);"><i class="fa-solid fa-star"></i> Ideal AI Model Answer:</strong>
                    <p style="color:#a7f3d0; margin-top:0.25rem;">"${e.ideal_answer}"</p>
                </div>

                <div style="color:var(--accent-cyan); font-size:0.82rem; margin-top:0.3rem;">
                    <strong>AI Evaluation Feedback:</strong> ${e.feedback}
                </div>
            `;
            testEvalResultsContainer.appendChild(div);
        });
    }

    // PDF Notes Download Helper
    window.downloadPdfNotes = async function(skillName) {
        if (!authToken) {
            authModal.classList.remove("hidden");
            alert("Please log in or create an account to download PDF Study Notes.");
            return;
        }

        try {
            const res = await fetch(`/api/notes/download/${encodeURIComponent(skillName)}`, {
                headers: { "Authorization": `Bearer ${authToken}` }
            });

            if (!res.ok) {
                if (res.status === 403) {
                    pricingModal.classList.remove("hidden");
                    alert("⚠️ PDF Study Notes are an exclusive Pro Feature (₹150/month). Upgrade to download!");
                    return;
                }
                throw new Error("Failed to download PDF notes.");
            }

            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `${skillName.replace(/\s+/g, '_')}_OpenAI_Study_Notes.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);

        } catch (err) {
            alert(`Download Error: ${err.message}`);
        }
    };

    btnCopyIp.addEventListener("click", () => {
        const textToCopy = networkUrl || window.location.href;
        navigator.clipboard.writeText(textToCopy).then(() => {
            alert(`Copied Network URL to Clipboard:\n${textToCopy}\nShare this with any device on your Wi-Fi!`);
        });
    });

    // Mobile & Desktop Touch File Selection Handlers
    dropZone.addEventListener("click", (e) => {
        if (e.target !== btnRemoveFile && !btnRemoveFile.contains(e.target)) {
            fileInput.click();
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleSelectedFile(e.target.files[0]);
        }
    });

    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) {
            handleSelectedFile(e.dataTransfer.files[0]);
        }
    });

    function handleSelectedFile(file) {
        const validExts = [".pdf", ".jpg", ".jpeg", ".png"];
        const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
        if (!validExts.includes(ext)) {
            alert(`Invalid file format '${ext}'. Please upload PDF, JPG, JPEG, or PNG.`);
            return;
        }
        selectedFile = file;
        fileNameText.textContent = file.name;
        fileSizeText.textContent = formatBytes(file.size);

        if (ext === ".pdf") {
            fileTypeIcon.className = "fa-solid fa-file-pdf file-type-icon";
            fileTypeIcon.style.color = "#f43f5e";
        } else {
            fileTypeIcon.className = "fa-solid fa-file-image file-type-icon";
            fileTypeIcon.style.color = "#06b6d4";
        }

        dropZone.querySelector(".drop-zone-content").classList.add("hidden");
        filePreviewBadge.classList.remove("hidden");
        btnScan.disabled = false;
    }

    btnRemoveFile.addEventListener("click", (e) => {
        e.stopPropagation();
        selectedFile = null;
        fileInput.value = "";
        dropZone.querySelector(".drop-zone-content").classList.remove("hidden");
        filePreviewBadge.classList.add("hidden");
        btnScan.disabled = true;
    });

    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return "0 Bytes";
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ["Bytes", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
    }

    btnScan.addEventListener("click", async () => {
        if (!selectedFile) return;

        btnScan.disabled = true;
        loaderContainer.classList.remove("hidden");
        resultsSection.classList.add("hidden");
        loaderText.textContent = selectedFile.name.endsWith(".pdf") 
            ? "Extracting PDF text and parsing skills..." 
            : "Running OCR image recognition across domain taxonomies...";

        const formData = new FormData();
        formData.append("file", selectedFile);
        if (targetJobSelect.value) {
            formData.append("target_job", targetJobSelect.value);
        }

        const headers = {};
        if (authToken) {
            headers["Authorization"] = `Bearer ${authToken}`;
        }

        try {
            const response = await fetch("/api/scan", {
                method: "POST",
                headers: headers,
                body: formData
            });

            let data;
            const contentType = response.headers.get("content-type") || "";
            if (contentType.includes("application/json")) {
                data = await response.json();
            } else {
                const textErr = await response.text();
                if (response.status === 502 || response.status === 503 || textErr.includes("<!DOCTYPE")) {
                    throw new Error("Server build is currently deploying on Render. Please wait 15 seconds for deployment to finish and click Scan again!");
                }
                throw new Error(`Server error status ${response.status}`);
            }

            if (!response.ok || !data.success) {
                if (response.status === 429) {
                    pricingModal.classList.remove("hidden");
                }
                throw new Error(data.detail || "Failed to analyze resume.");
            }

            if (data.user) {
                updateAuthUI(data.user);
            }

            currentScanData = data;
            renderResults(data);

        } catch (error) {
            alert(`${error.message}`);
        } finally {
            loaderContainer.classList.add("hidden");
            btnScan.disabled = false;
        }
    });

    // Render Full Results
    function renderResults(data) {
        document.getElementById("resCandidateName").textContent = `Analysis for ${data.filename}`;
        document.getElementById("resEmail").innerHTML = `<i class="fa-regular fa-envelope"></i> ${data.contact_info.email}`;
        document.getElementById("resPhone").innerHTML = `<i class="fa-solid fa-phone"></i> ${data.contact_info.phone}`;
        document.getElementById("resExp").innerHTML = `<i class="fa-solid fa-user-clock"></i> ${data.experience_level}`;
        document.getElementById("resFileType").innerHTML = `<i class="fa-solid fa-file-code"></i> ${data.file_type} ${data.ocr_used ? '(OCR Active)' : ''}`;

        // ATS Audit Rendering
        const ats = data.ats_audit;
        document.getElementById("resAtsScore").textContent = `${ats.overall_ats_score}%`;
        document.getElementById("atsContactVal").textContent = `${ats.contact_score}/25`;
        document.getElementById("atsContactFill").style.width = `${(ats.contact_score / 25) * 100}%`;

        document.getElementById("atsVerbVal").textContent = `${ats.verb_score}/25`;
        document.getElementById("atsVerbFill").style.width = `${(ats.verb_score / 25) * 100}%`;

        document.getElementById("atsKeywordVal").textContent = `${ats.keyword_score}/25`;
        document.getElementById("atsKeywordFill").style.width = `${(ats.keyword_score / 25) * 100}%`;

        document.getElementById("atsStructVal").textContent = `${ats.structural_score}/25`;
        document.getElementById("atsStructFill").style.width = `${(ats.structural_score / 25) * 100}%`;

        const warningsBox = document.getElementById("atsWarningsBox");
        warningsBox.innerHTML = "";
        ats.warnings.forEach(w => {
            const div = document.createElement("div");
            div.className = "ats-warning-item";
            div.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-amber"></i> ${w}`;
            warningsBox.appendChild(div);
        });
        ats.recommendations.forEach(r => {
            const div = document.createElement("div");
            div.className = "ats-recommendation-item";
            div.innerHTML = `<i class="fa-solid fa-lightbulb text-cyan"></i> ${r}`;
            warningsBox.appendChild(div);
        });

        // Market Analytics Rendering
        const jobAnalysis = data.target_job_analysis;
        document.getElementById("mktFresherSalary").textContent = jobAnalysis.fresher_salary;
        document.getElementById("mktExpSalary").textContent = jobAnalysis.experienced_salary;
        document.getElementById("mktDemandTag").textContent = jobAnalysis.market_demand;

        const companyTagsContainer = document.getElementById("mktCompanyTags");
        companyTagsContainer.innerHTML = "";
        jobAnalysis.hiring_companies.forEach(comp => {
            const tag = document.createElement("span");
            tag.className = "tag-company";
            tag.textContent = comp;
            companyTagsContainer.appendChild(tag);
        });

        // Target Match Info
        document.getElementById("resJobTitle").textContent = jobAnalysis.title;
        document.getElementById("resMatchPercentage").textContent = `${jobAnalysis.match_percentage}%`;
        document.getElementById("resSkillsFoundCount").textContent = jobAnalysis.matched_count;
        document.getElementById("resMissingCount").textContent = jobAnalysis.missing_skills.total_missing;

        const scoreCircleWrapper = document.querySelector(".score-circle-wrapper");
        const scorePct = jobAnalysis.match_percentage;
        scoreCircleWrapper.style.background = `conic-gradient(var(--accent-purple) 0%, var(--primary) ${scorePct}%, rgba(255, 255, 255, 0.1) ${scorePct}%)`;

        const highPriorityContainer = document.getElementById("highPriorityTags");
        const medPriorityContainer = document.getElementById("medPriorityTags");
        highPriorityContainer.innerHTML = "";
        medPriorityContainer.innerHTML = "";

        if (jobAnalysis.missing_skills.high_priority.length > 0) {
            jobAnalysis.missing_skills.high_priority.forEach(skill => {
                const tag = document.createElement("span");
                tag.className = "tag-missing-high";
                tag.textContent = skill;
                highPriorityContainer.appendChild(tag);
            });
        } else {
            highPriorityContainer.innerHTML = `<span class="chip" style="color:#10b981;">✓ All core requirements met!</span>`;
        }

        if (jobAnalysis.missing_skills.medium_priority.length > 0) {
            jobAnalysis.missing_skills.medium_priority.forEach(skill => {
                const tag = document.createElement("span");
                tag.className = "tag-missing-med";
                tag.textContent = skill;
                medPriorityContainer.appendChild(tag);
            });
        } else {
            medPriorityContainer.innerHTML = `<span class="chip">No optional skill gaps detected</span>`;
        }

        const catSkillsContainer = document.getElementById("categorizedSkillsContainer");
        catSkillsContainer.innerHTML = "";

        const categorized = data.categorized_skills;
        if (Object.keys(categorized).length > 0) {
            for (const [catName, skills] of Object.entries(categorized)) {
                const block = document.createElement("div");
                block.className = "category-block";

                const catTitle = document.createElement("div");
                catTitle.className = "cat-title";
                catTitle.textContent = catName;

                const tagsDiv = document.createElement("div");
                tagsDiv.className = "extracted-tags";

                skills.forEach(s => {
                    const tag = document.createElement("span");
                    tag.className = "tag-skill";
                    tag.textContent = s;
                    tagsDiv.appendChild(tag);
                });

                block.appendChild(catTitle);
                block.appendChild(tagsDiv);
                catSkillsContainer.appendChild(block);
            }
        }

        const jobRecsList = document.getElementById("jobRecsList");
        jobRecsList.innerHTML = "";
        data.all_job_recommendations.slice(0, 6).forEach(rec => {
            const item = document.createElement("div");
            item.className = "job-rec-item";
            item.innerHTML = `
                <div>
                    <div class="rec-title">${rec.title}</div>
                    <div class="rec-domain">${rec.stream} &bull; ${rec.domain}</div>
                </div>
                <div class="rec-match-badge">${rec.match_percentage}% Match</div>
            `;
            jobRecsList.appendChild(item);
        });

        // Roadmap Cards Rendering
        const roadmapGrid = document.getElementById("roadmapGrid");
        roadmapGrid.innerHTML = "";
        const isPro = currentUser && currentUser.is_pro;

        if (jobAnalysis.upskill_recommendations.length > 0) {
            jobAnalysis.upskill_recommendations.forEach(up => {
                const card = document.createElement("div");
                card.className = "roadmap-item";

                if (isPro) {
                    card.innerHTML = `
                        <div class="roadmap-skill"><i class="fa-solid fa-crown text-amber"></i> ${up.skill} <span class="pro-resource-badge">PRO KIT</span></div>
                        <div class="roadmap-desc" style="margin-bottom:0.75rem;">${up.suggestion}</div>
                        
                        <div class="pro-resources-box">
                            <div class="res-item">
                                <i class="fa-brands fa-youtube text-rose"></i>
                                <div>
                                    <strong>${up.video_title || up.skill + ' Video Course'}</strong><br/>
                                    <a href="${up.video_url}" target="_blank" class="btn-res-link">📺 Watch Video Course</a>
                                </div>
                            </div>
                            <div class="res-item">
                                <i class="fa-solid fa-file-pdf text-cyan"></i>
                                <div>
                                    <strong>${up.notes_title || up.skill + ' Study Notes'}</strong><br/>
                                    <button class="btn-res-link" style="background:rgba(6,182,212,0.2); color:#a5f3fc; border:1px solid rgba(6,182,212,0.4); margin-top:0.25rem;" onclick="downloadPdfNotes('${up.skill.replace(/'/g, "\\'")}')">
                                        📄 Download OpenAI PDF Notes
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                } else {
                    card.innerHTML = `
                        <div class="roadmap-skill"><i class="fa-solid fa-lightbulb text-amber"></i> ${up.skill}</div>
                        <div class="roadmap-desc" style="margin-bottom:0.75rem;">${up.suggestion}</div>
                        
                        <div class="locked-pro-box">
                            <div class="locked-text">
                                <i class="fa-solid fa-lock text-amber"></i> 
                                <span><strong>OpenAI PDF Notes & Video Masterclass Locked</strong></span>
                            </div>
                            <p style="font-size:0.78rem; color:var(--text-muted); margin-bottom:0.6rem;">
                                Upgrade to Pro (₹150/mo) to unlock Multi-Page OpenAI Study Masterclasses for ${up.skill}.
                            </p>
                            <button class="btn-unlock-skill-pro" onclick="document.getElementById('pricingModal').classList.remove('hidden')">
                                👑 Unlock OpenAI PDF Notes (₹150/mo)
                            </button>
                        </div>
                    `;
                }
                roadmapGrid.appendChild(card);
            });
        }

        resultsSection.classList.remove("hidden");
        
        // Smooth scroll for mobile & desktop
        window.scrollTo({
            top: resultsSection.offsetTop - 30,
            behavior: "smooth"
        });
    }

    btnPrintReport.addEventListener("click", () => {
        window.print();
    });
});
