# DarkStream

A local Flask video library. It saves each uploaded video in `uploads/` and remembers titles and dates in `videos.db`.

## Run it on Windows

1. Open this `darkstream` folder in VS Code.
2. Select **Terminal → New Terminal**.
3. Run the following command once to install Flask:

   ```powershell
   py -m pip install -r requirements.txt
   ```

4. Start the website:

   ```powershell
   py app.py
   ```

5. Open this address in your browser:

   ```text
   http://127.0.0.1:5000
   ```

Press `Ctrl + C` in the VS Code terminal to stop the website.

## Notes

- This is a local learning project. It is not ready for public deployment or for storing sensitive/private material on a shared computer.
- Videos and their details survive a restart because they are stored in the `uploads/` folder and `videos.db` database.
- The app accepts common video filename extensions, but filename validation alone is not sufficient protection for a public website.
