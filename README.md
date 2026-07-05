# 🚀 Rocket 2D

A fast-paced 2D arcade soccer game inspired by rocket-powered vehicle gameplay. Control your rocket, hit the ball, score goals, and challenge either AI or another player in exciting matches.

> Built with **Python** and **Pygame Community Edition (pygame-ce)**.

---

## ✨ Features

- 🚗 Rocket-powered vehicle movement
- ⚽ Physics-based ball gameplay
- 🤖 AI opponent
- 👥 Local multiplayer support
- 🔊 Sound effects and background music
- 💾 Save system
- 🎮 Smooth arcade-style gameplay
- 🖥️ Clean and organized project structure

---

## 📂 Project Structure

```
Rocket 2D/
├── assets/
│   ├── audio/
│   └── generated/
├── rocket2d/
│   ├── ai.py
│   ├── arenas.py
│   ├── assets.py
│   ├── bootstrap.py
│   ├── camera.py
│   ├── constants.py
│   ├── entities.py
│   ├── game.py
│   ├── math2d.py
│   ├── particles.py
│   ├── persistence.py
│   ├── scenes.py
│   ├── settings.py
│   └── ui.py
├── save/
├── main.py
└── requirements.txt
```

---

## 🛠 Requirements

- Python **3.10+**
- pygame-ce

Install the required packages:

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Game

Start the game with:

```bash
python main.py
```

Run the built-in self test:

```bash
python main.py --self-test
```

---

## 🎮 Controls

| Action | Key |
|---------|-----|
| Move Left | A / Left Arrow |
| Move Right | D / Right Arrow |
| Jump | Space |
| Boost | Left Shift |

> Controls may vary depending on the selected game mode.

---

## 💾 Save Data

Game progress and settings are stored inside:

```
save/
```

Deleting this folder will reset local progress.

---

## 📦 Dependencies

- Python
- pygame-ce

---

## 📜 License

This project is licensed under the MIT License.

See the **LICENSE** file for more information.

---

## 🤝 Contributing

Contributions, suggestions, and bug reports are welcome.

Feel free to fork the project and submit a pull request.

---

## 📸 Screenshots

Add screenshots of your gameplay here.

```
assets/screenshots/gameplay.png
```

---

## 👨‍💻 Author

Created by **cinary09**

GitHub: https://github.com/yourusername

---

## ⭐ Support

If you enjoyed this project, consider giving it a ⭐ on GitHub. It helps the project reach more people and motivates future updates.
