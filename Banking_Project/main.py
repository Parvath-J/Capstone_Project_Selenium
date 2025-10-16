# filename: main.py
from database import DB  # <-- This line was corrected
from gui import BankingApp

if __name__ == '__main__':
    # 1. Establish the database connection
    db_connection = DB()

    # 2. Create an instance of the main GUI class
    app = BankingApp(db_connection)

    # 3. Start the application's main loop
    app.mainloop()