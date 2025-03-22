const express = require("express");
const path = require("path");
const { Pool } = require("pg");
const cookieParser = require("cookie-parser");
const shortUUID = require("short-uuid");
const requestIp = require("request-ip");
require("dotenv").config();

const app = express();
const PORT = process.env.PORT || 3000;

const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
});

pool.connect()
    .then(() => console.log("✅ PostgreSQL Connected"))
    .catch((err) => console.error("❌ PostgreSQL Connection Error:", err));

app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));

app.use(express.static(path.join(__dirname, "public")));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());
app.use(requestIp.mw());

app.get("/", (req, res) => res.render("home", { title: "Home - Seerat Web" }));
app.get("/hadith", (req, res) => res.render("hadith", { title: "Daily Hadith" }));
app.get("/history", (req, res) => res.render("history", { title: "Historical Places" }));
app.get("/ilmbot", (req, res) => res.render("ilmbot", { title: "IlmBot - Ask Questions" }));
app.get("/kids-corner", (req, res) => res.render("kids-corner", { title: "Kids Corner" }));
app.get("/quiz", (req, res) => res.render("quiz", { title: "Seerat Quiz" }));
app.get("/resources", (req, res) => res.render("resources", { title: "Seerat Resources" }));
app.get("/videos", (req, res) => res.render("videos", { title: "Video Lectures" }));
app.get("/contact", (req, res) => res.render("contact", { title: "Contact" }));

app.post("/submit-form", async (req, res) => {
    try {
        const { name, email, subject, message } = req.body;

        const result = await pool.query(
            "INSERT INTO form (name, email, subject, message) VALUES ($1, $2, $3, $4) RETURNING *",
            [name, email, subject, message]
        );

        res.json({ success: true, message: "Message saved successfully!", data: result.rows[0] });
    } catch (error) {
        console.error("❌ Error saving message:", error);
        res.status(500).json({ success: false, error: "Server error" });
    }
});

app.post("/track-user", async (req, res) => {
    try {
        let userId = req.cookies.user_id;
        const ipAddress = req.clientIp || req.ip;

        if (!userId) {
            userId = shortUUID.generate();
            res.cookie("user_id", userId, {
                httpOnly: true,
                secure: process.env.NODE_ENV === "production",
                maxAge: 365 * 24 * 60 * 60 * 1000, 
            });
        }

        await pool.query(
            "INSERT INTO users (user_id, ip_address) VALUES ($1, $2) ON CONFLICT (user_id) DO NOTHING",
            [userId, ipAddress]
        );

        res.json({ success: true, user_id: userId });
    } catch (err) {
        console.error("❌ Database error:", err);
        res.status(500).json({ success: false, error: "Database error" });
    }
});

app.use((req, res) => {
    res.status(404).render("404", { title: "Page Not Found" });
});

app.listen(PORT, () => {
    console.log(`🚀 Server running at http://localhost:${PORT}`);
});
