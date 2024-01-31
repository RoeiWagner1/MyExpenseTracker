# -*- coding: utf-8 -*-
import datetime
import sqlite3
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext, \
    CallbackQueryHandler

TOKEN = 0
# Read the token from the config file
with open('config_exp.txt') as file:
    lines = file.readlines()
    for line in lines:
        key, value = line.strip().split('=')
        if key == 'TOKEN':
            TOKEN = value

# Connect to the SQLite database
conn = sqlite3.connect('my_wallet.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        bank_account REAL    
    )
''')
conn.commit()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        exp_entry INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category TEXT,
        month INTEGER,
        year INTEGER,
        description TEXT,
        amount REAL,
        FOREIGN KEY(user_id) REFERENCES Users(user_id)
    )
''')
conn.commit()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS income (
        inc_entry INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category TEXT,
        month INTEGER,
        year INTEGER,
        description TEXT,
        amount REAL,
        FOREIGN KEY(user_id) REFERENCES Users(user_id)
    )
''')
conn.commit()


async def display_main_menu(user_id, context: CallbackContext):
    bold_text = "<b>Main Menu:</b>"
    keyboard = [
        [
            InlineKeyboardButton("Profile Settings", callback_data='settings')
        ],
        [
            InlineKeyboardButton("Balance Overview", callback_data='overview')
        ],
        [
            InlineKeyboardButton("Manage Finances", callback_data='manage')
        ],
        [
            InlineKeyboardButton("Expenses & Income", callback_data='exp&inc')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(user_id, text=bold_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if not result:
        await context.bot.send_message(user_id,
                                       text="Hello! \nAccording to the information I have, it seems you haven't created a profile yet. \nTo get started, please press /start")
    else:
        await display_main_menu(user_id, context)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    await context.bot.send_message(user_id,
                                   text="Welcome! I'm your new expense tracker bot 😊\n\nHere, you can manage your monthly expenses and income. \nFeel free to add, edit, and track your financial transactions. \nYou can even keep an eye on your bank account balance!\n\nEnjoy!")
    await start_respond(user_id, context)


async def start_respond(user_id, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if result:
        user_name = result[1]
        user_last_name = result[2]
        await context.bot.send_message(user_id, text=f"Hello {user_name} {user_last_name}!\nWhat would you like to do?")
        await display_main_menu(user_id, context)

    else:
        keyboard = [
            [
                InlineKeyboardButton("START", callback_data='start')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(user_id, "<b>When you're ready, press the button!</b>",
                                       reply_markup=reply_markup, parse_mode=ParseMode.HTML)


async def profile_settings(user_id, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("Update Profile", callback_data='edit_profile')
        ],
        [
            InlineKeyboardButton("Reset Database", callback_data='reset_database')
        ],
        [
            InlineKeyboardButton("Back to Menu", callback_data='back_to_menu')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(user_id, text="What would you like to do?", reply_markup=reply_markup)


async def edit_settings(user_id, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("First Name", callback_data='First Name_edit')
        ],
        [
            InlineKeyboardButton("Last Name", callback_data='Last Name_edit')
        ],
        [
            InlineKeyboardButton("Bank Account Balance", callback_data='Bank Account Balance_edit')
        ],
        [
            InlineKeyboardButton("Back to Menu", callback_data="back_to_set")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(user_id, text="Which field do you want to edit?", reply_markup=reply_markup)


async def reset_database(user_id, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("Yes, Reset Database", callback_data='confirm_reset')
        ],
        [
            InlineKeyboardButton("Cancel", callback_data='cancel_reset')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(user_id,
                                   text="This action will permanently delete all your entered data, including your profile.")
    await context.bot.send_message(user_id, text="<b>Are you sure you want to proceed?</b>", reply_markup=reply_markup,
                                   parse_mode=ParseMode.HTML)


async def monthly_expenses(user_id, context: CallbackContext):
    month = datetime.datetime.now().month
    year = datetime.datetime.now().year
    category = 'החזרים באשראי'
    total = 0

    cursor.execute('SELECT amount FROM expenses WHERE user_id = ? AND month = ? AND year = ? AND category != ?',
                   (user_id, month, year, "תנועות חשבון"))
    results = cursor.fetchall()
    if results:
        for row in results:
            total += row[0]

    cursor.execute('SELECT amount FROM income WHERE user_id = ? AND month = ? AND year = ? AND category = ?',
                   (user_id, month, year, category))
    results = cursor.fetchall()
    if results:
        for row in results:
            total -= row[0]

    return round(total, 2)


async def monthly_income(user_id, context: CallbackContext):
    month = datetime.datetime.now().month
    year = datetime.datetime.now().year
    category = 'החזרים באשראי'
    total = 0

    cursor.execute('SELECT amount FROM income WHERE user_id = ? AND month = ? AND year = ? AND category != ?',
                   (user_id, month, year, category))
    results = cursor.fetchall()
    if results:
        for row in results:
            total += row[0]

    cursor.execute('SELECT amount FROM expenses WHERE user_id = ? AND month = ? AND year = ? AND category = ?',
                   (user_id, month, year, "תנועות חשבון"))
    results = cursor.fetchall()
    if results:
        for row in results:
            total -= row[0]

    return round(total, 2)


async def balance_overview_command(user_id, context: CallbackContext):
    cursor.execute('SELECT first_name, last_name, bank_account FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    first_name, last_name, bank_account = result
    month_exp = await monthly_expenses(user_id, context)
    month_inc = await monthly_income(user_id, context)

    if bank_account:
        bank_account += month_inc
        remain = round((bank_account - month_exp), 2)
        await context.bot.send_message(user_id,
                                       text=f"<b>Hello {first_name} {last_name}!</b>\n\nUntil this day, there is {bank_account} NIS in your bank account.\n\nYour total expenses this month is: {month_exp} NIS\n\nYour total income this month is: {month_inc} NIS\n\nOn the billing date, {remain} NIS will be remaining in your bank account.\n\nPress /menu to return to the Main Menu.",
                                       parse_mode=ParseMode.HTML)

    else:
        await context.bot.send_message(user_id,
                                       text=f"<b>Hello {first_name} {last_name}!</b>\n\nYour total expenses this month is: {month_exp} NIS.\n\nYour total income this month is: {month_inc} NIS.\n\nPress /menu to return to the Main Menu.",
                                       parse_mode=ParseMode.HTML)


async def manage_finances_command(user_id, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("Add", callback_data='add')
        ],
        [
            InlineKeyboardButton("Edit", callback_data='edit')
        ],
        [
            InlineKeyboardButton("Delete", callback_data='delete')
        ],
        [
            InlineKeyboardButton("Back to Menu", callback_data='back_to_menu')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(user_id, text="What would you like to do?", reply_markup=reply_markup)


async def add_expense(user_id, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("חשבונות", callback_data='חשבונות_הו')
        ],
        [
            InlineKeyboardButton("ברים ומסעדות", callback_data='ברים ומסעדות_הו')
        ],
        [
            InlineKeyboardButton("פנאי ובידור", callback_data='פנאי ובידור_הו')
        ],
        [
            InlineKeyboardButton("חופשות", callback_data='חופשות_הו')
        ],
        [
            InlineKeyboardButton("מחייה", callback_data='מחייה_הו')
        ],
        [
            InlineKeyboardButton("תחבורה", callback_data='תחבורה_הו')
        ],
        [
            InlineKeyboardButton("לימודים/עבודה", callback_data='לימודים/עבודה_הו')
        ],
        [
            InlineKeyboardButton("קניות", callback_data='קניות_הו')
        ],
        [
            InlineKeyboardButton("הוראות קבע", callback_data='הוראות קבע_הו')
        ],
        [
            InlineKeyboardButton("שכירות", callback_data='שכירות_הו')
        ],
        [
            InlineKeyboardButton("תנועות חשבון", callback_data='תנועות חשבון_הו')
        ],
        [
            InlineKeyboardButton("הוצאות נוספות", callback_data='הוצאות נוספות_הו')
        ],
        [
            InlineKeyboardButton("Back to Menu", callback_data='back_to_manage')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(user_id, text="Select a Category:", reply_markup=reply_markup)
    year = datetime.datetime.now().year
    await context.bot.send_message(user_id,
                                   text=f"<b>Attention!</b>\n\nExpense entries will be recorded for the current year ({year}).\nTo change the year, use the 'Manage Finances' button in the Main Menu (/menu)",
                                   parse_mode=ParseMode.HTML)


async def add_income(user_id, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("משכורת", callback_data='משכורת_הכ')
        ],
        [
            InlineKeyboardButton("העברות מאפליקציה", callback_data='העברות מאפליקציה_הכ')
        ],
        [
            InlineKeyboardButton("תנועות חשבון", callback_data='תנועות חשבון_הכ')
        ],
        [
            InlineKeyboardButton("החזרים באשראי", callback_data='החזרים באשראי_הכ')
        ],
        [
            InlineKeyboardButton("הכנסות נוספות", callback_data='הכנסות נוספות_הכ')
        ],
        [
            InlineKeyboardButton("Back to Menu", callback_data='back_to_manage')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(user_id, text="Select a Category:", reply_markup=reply_markup)
    year = datetime.datetime.now().year
    await context.bot.send_message(user_id,
                                   text=f"<b>Attention!</b>\n\nIncome entries will be recorded for the current year ({year}).\nTo change the year, use the 'Manage Finances' button in the Main Menu (/menu)",
                                   parse_mode=ParseMode.HTML)


async def display_exp_and_inc(user_id, month, context: CallbackContext):
    cursor.execute('''
        SELECT exp_entry, description, category, amount
        FROM expenses
        WHERE user_id = ? AND month = ? AND year = ?
        ORDER BY category
    ''', (user_id, month, context.user_data['year']))
    expenses_data = cursor.fetchall()

    cursor.execute('''
        SELECT inc_entry, description, category, amount
        FROM income
        WHERE user_id = ? AND month = ? AND year = ?
        ORDER BY category
    ''', (user_id, month, context.user_data['year']))
    income_data = cursor.fetchall()

    # Create a dictionary to group expenses by category
    expenses_by_category = {}
    for row in expenses_data:
        exp_entry, description, category, amount = row
        if category not in expenses_by_category:
            expenses_by_category[category] = []
        expenses_by_category[category].append((exp_entry, amount, description))

    # Create a dictionary to group income by category
    income_by_category = {}
    for row in income_data:
        inc_entry, description, category, amount = row
        if category not in income_by_category:
            income_by_category[category] = []
        income_by_category[category].append((inc_entry, amount, description))

    # Format and display Expenses
    view_message = "<b>הוצאות</b>"
    for category, entries in expenses_by_category.items():
        view_message += f"\n<u>{category}</u>\n"
        for entry in entries:
            view_message += "({:})  {:<10} {:<20}\n".format(entry[0], entry[1], entry[2])

    # Format and display Income
    view_message += "\n\n<b>הכנסות</b>"
    for category, entries in income_by_category.items():
        view_message += f"\n<u>{category}</u>\n"
        for entry in entries:
            view_message += "({:})  {:<10} {:<20}\n".format(entry[0], entry[1], entry[2])

    # Send messages
    view_message += "\n\nPress /menu to return to the Menu."
    await context.bot.send_message(user_id, text=view_message, parse_mode=ParseMode.HTML)


async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.message.chat_id
    data = query.data

    if data == 'start':
        await context.bot.send_message(user_id,
                                       text="Before we start, i'll need some details :)\nDon't worry, you can always update them!")
        await context.bot.send_message(user_id, text="What is your first name?")
        context.user_data['pending_action'] = 'first_time_name'

    elif data == 'yes_bank':
        await context.bot.send_message(user_id, text="Please enter your current bank account balance:")
        context.user_data['pending_action'] = 'first_time_bank'

    elif data == 'no_bank':
        context.user_data['bank_account'] = None
        keyboard = [
            [
                InlineKeyboardButton("Yes", callback_data='yes_exp'),
                InlineKeyboardButton("No", callback_data='no_exp')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(user_id,
                                       text="Do you have expenses or income this month?",
                                       reply_markup=reply_markup)

    elif data == 'yes_exp':
        await context.bot.send_message(user_id, text="Please provide your total expenses for this month:")
        context.user_data['pending_action'] = 'first_time_exp'

    elif data == 'no_exp':
        cursor.execute(
            'INSERT OR REPLACE INTO users (user_id, first_name, last_name, bank_account)'
            'VALUES (?, ?, ?, ?)',
            (
                user_id,
                context.user_data['first_name'],
                context.user_data['last_name'],
                None
            ))
        conn.commit()

        if context.user_data['bank_account']:
            cursor.execute(f'UPDATE users SET bank_account = ? WHERE user_id = ?',
                           (context.user_data['bank_account'], user_id))
            conn.commit()

        await context.bot.send_message(user_id, text="We are done! Thank you for your cooperation")
        await display_main_menu(user_id, context)
        context.user_data.clear()

    elif data == "back_to_menu":
        await display_main_menu(user_id, context)
    elif data == 'back_to_set':
        await profile_settings(user_id, context)
    elif data == 'back_to_manage':
        await manage_finances_command(user_id, context)
    elif data == 'settings':
        await profile_settings(user_id, context)
    elif data == 'manage':
        await manage_finances_command(user_id, context)

    elif data == 'reset_database':
        await reset_database(user_id, context)
    elif data == 'cancel_reset':
        await display_main_menu(user_id, context)
    elif data == 'confirm_reset':
        cursor.execute('DELETE FROM expenses WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM income WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        conn.commit()
        message = "Database reset is completed. \nAll data has been erased. \n\nIf you want to start over type /start"
        await context.bot.send_message(user_id, text=message)

    elif data == 'edit_profile':
        await edit_settings(user_id, context)

    elif data == 'First Name_edit' or data == 'Last Name_edit' or data == 'Bank Account Balance_edit':
        field = data.split("_", 1)[0]
        if field == "Bank Account Balance":
            keyboard = [
                [
                    InlineKeyboardButton("Update Bank Account Balance", callback_data='update_balance')
                ],
                [
                    InlineKeyboardButton("Start Monitoring Bank Account", callback_data='track_confirm')
                ],
                [
                    InlineKeyboardButton("Stop Monitoring Bank Account", callback_data='track_cancel')
                ],
                [
                    InlineKeyboardButton("Back to Menu", callback_data='back_to_set')
                ]

            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(user_id,
                                           text="What would you like to do?",
                                           reply_markup=reply_markup)

        else:
            await context.bot.send_message(user_id, f"Enter the new {field}:")
            if field == "First Name":
                field = "first name"
            if field == "Last Name":
                field = "last name"
            context.user_data['pending_action'] = f'edit_settings_{field}'

    elif data == 'track_confirm':
        cursor.execute('SELECT bank_account FROM users WHERE user_id = ? ', (user_id,))
        results = cursor.fetchone()
        if results[0]:
            await context.bot.send_message(user_id, "I'm already tracking your bank account!")
            await edit_settings(user_id, context)
        else:
            await context.bot.send_message(user_id, f"Enter the new Bank Account Balance:")
            context.user_data['pending_action'] = f'edit_settings_bank account'

    elif data == 'update_balance':
        cursor.execute('SELECT bank_account FROM users WHERE user_id = ? ', (user_id,))
        results = cursor.fetchone()
        if results[0]:
            await context.bot.send_message(user_id, f"Enter the new Bank Account Balance:")
            context.user_data['pending_action'] = f'edit_settings_bank account'
        else:
            await context.bot.send_message(user_id,
                                           "You've chosen not to track your bank account.\n\nIf you'd like to change this setting, click on the 'Start Monitoring Bank Account' button.")
            await edit_settings(user_id, context)

    elif data == 'track_cancel':
        cursor.execute(f'UPDATE users SET bank_account = ? WHERE user_id = ?',
                       (None, user_id,))
        conn.commit()
        await context.bot.send_message(user_id,
                                       "You've chosen not to track your bank account.\n\nIf you'd like to change this setting, click on the 'Start Monitoring Bank Account' button.")
        await edit_settings(user_id, context)

    elif data == 'overview':
        await balance_overview_command(user_id, context)

    elif data == 'add' or data == 'edit' or data == 'delete':
        keyboard = [
            [
                InlineKeyboardButton("Income", callback_data=f'{data}_income'),
                InlineKeyboardButton("Expense", callback_data=f'{data}_expense')
            ],
            [
                InlineKeyboardButton("Back to Menu", callback_data='back_to_manage')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(user_id, text="Choose:", reply_markup=reply_markup)

    elif data == "add_income" or data == "add_expense":
        split_data = data.split("_", 1)[-1]
        if split_data == "income":
            await add_income(user_id, context)
        else:
            await add_expense(user_id, context)

    elif data == "edit_income" or data == "edit_expense":
        data_split = data.split("_")[1]
        await context.bot.send_message(user_id,
                                       text=f"Enter the {data_split} number you want to edit:\n\n(You can find the number by clicking on the 'Expenses & Income' button in the Main Menu)")
        context.user_data['pending_action'] = f"{data_split}_entry"

    elif data == "income_Month" or data == "expense_Month" or data == "income_Year" or data == "expense_Year" or data == "income_Description" or data == "expense_Description" or data == "income_Amount" or data == "expense_Amount":
        split_category = data.split("_")[1]
        exp_or_inc = data.split("_")[0]
        response_message = f"Enter the new {split_category}:"
        if split_category == "Month":
            response_message += "\n\n(Use a number - 10 for October)"
        if split_category == "Year":
            response_message += "\n\n(Use 4 digits - for example 2023)"
        await context.bot.send_message(user_id, text=response_message)
        context.user_data['pending_action'] = f"new_{exp_or_inc}_{split_category}"

    elif data == "income_Category" or data == "expense_Category":
        exp_or_inc = data.split("_")[0]
        if exp_or_inc == "income":
            keyboard = [
                [
                    InlineKeyboardButton("משכורת", callback_data='משכורת_הכנ')
                ],
                [
                    InlineKeyboardButton("העברות מאפליקציה", callback_data='העברות מאפליקציה_הכנ')
                ],
                [
                    InlineKeyboardButton("תנועות חשבון", callback_data='תנועות חשבון_הכנ')
                ],
                [
                    InlineKeyboardButton("החזרים באשראי", callback_data='החזרים באשראי_הכנ')
                ],
                [
                    InlineKeyboardButton("הכנסות נוספות", callback_data='הכנסות נוספות_הכנ')
                ],
                [
                    InlineKeyboardButton("Back to Menu", callback_data='back_to_manage')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(user_id, text="Select a Category:", reply_markup=reply_markup)

        else:
            keyboard = [
                [
                    InlineKeyboardButton("חשבונות", callback_data='חשבונות_הוצ')
                ],
                [
                    InlineKeyboardButton("ברים ומסעדות", callback_data='ברים ומסעדות_הוצ')
                ],
                [
                    InlineKeyboardButton("פנאי ובידור", callback_data='פנאי ובידור_הוצ')
                ],
                [
                    InlineKeyboardButton("חופשות", callback_data='חופשות_הוצ')
                ],
                [
                    InlineKeyboardButton("מחייה", callback_data='מחייה_הוצ')
                ],
                [
                    InlineKeyboardButton("תחבורה", callback_data='תחבורה_הוצ')
                ],
                [
                    InlineKeyboardButton("לימודים/עבודה", callback_data='לימודים/עבודה_הוצ')
                ],
                [
                    InlineKeyboardButton("קניות", callback_data='קניות_הוצ')
                ],
                [
                    InlineKeyboardButton("הוראות קבע", callback_data='הוראות קבע_הוצ')
                ],
                [
                    InlineKeyboardButton("שכירות", callback_data='שכירות_הוצ')
                ],
                [
                    InlineKeyboardButton("תנועות חשבון", callback_data='תנועות חשבון_הוצ')
                ],
                [
                    InlineKeyboardButton("הוצאות נוספות", callback_data='הוצאות נוספות_הוצ')
                ],
                [
                    InlineKeyboardButton("Back to Menu", callback_data='back_to_manage')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(user_id, text="Select a Category:", reply_markup=reply_markup)

    elif data == 'חשבונות_הו' or data == 'תנועות חשבון_הו' or data == 'שכירות_הו' or data == 'ברים ומסעדות_הו' or data == 'פנאי ובידור_הו' or data == 'חופשות_הו' or data == 'מחייה_הו' or data == 'תחבורה_הו' or data == 'לימודים/עבודה_הו' or data == 'קניות_הו' or data == 'הוראות קבע_הו' or data == 'הוצאות נוספות_הו' or data == 'משכורת_הכ' or data == 'העברות מאפליקציה_הכ' or data == 'תנועות חשבון_הכ' or data == 'החזרים באשראי_הכ' or data == 'הכנסות נוספות_הכ':
        context.user_data['category'] = data
        keyboard = [
            [
                InlineKeyboardButton("1", callback_data='1'),
                InlineKeyboardButton("2", callback_data='2'),
                InlineKeyboardButton("3", callback_data='3'),
                InlineKeyboardButton("4", callback_data='4')
            ],
            [
                InlineKeyboardButton("5", callback_data='5'),
                InlineKeyboardButton("6", callback_data='6'),
                InlineKeyboardButton("7", callback_data='7'),
                InlineKeyboardButton("8", callback_data='8')
            ],
            [
                InlineKeyboardButton("9", callback_data='9'),
                InlineKeyboardButton("10", callback_data='10'),
                InlineKeyboardButton("11", callback_data='11'),
                InlineKeyboardButton("12", callback_data='12')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(user_id, text="Which month?", reply_markup=reply_markup)

    elif data == 'חשבונות_הוצ' or data == 'תנועות חשבון_הוצ' or data == 'שכירות_הוצ' or data == 'ברים ומסעדות_הוצ' or data == 'פנאי ובידור_הוצ' or data == 'חופשות_הוצ' or data == 'מחייה_הוצ' or data == 'תחבורה_הוצ' or data == 'לימודים/עבודה_הוצ' or data == 'קניות_הוצ' or data == 'הוראות קבע_הוצ' or data == 'הוצאות נוספות_הוצ' or data == 'משכורת_הכנ' or data == 'העברות מאפליקציה_הכנ' or data == 'תנועות חשבון_הכנ' or data == 'החזרים באשראי_הכנ' or data == 'הכנסות נוספות_הכנ':
        temp = data.split("_")[1]
        exp_and_inc = "income"
        if temp == "הוצ":
            exp_and_inc = "expenses"
            temp = "exp"
        else:
            temp = "inc"

        cursor.execute(f'UPDATE {exp_and_inc} SET category = ? WHERE user_id = ? AND {temp}_entry = ?',
                       (data.split("_")[0], user_id, context.user_data['entry']))
        conn.commit()

        await context.bot.send_message(user_id,
                                       "Done!\n\nTo view your details, use the 'Expenses & Income' button in the Main Menu (/menu)")
        await manage_finances_command(user_id, context)
        context.user_data.clear()

    elif data == "delete_income" or data == "delete_expense":
        data_split = data.split("_")[1]
        await context.bot.send_message(user_id,
                                       text=f"Enter the {data_split} number you want to delete:\n\n(You can find the number by clicking on the 'Expenses & Income' button in the Main Menu)")
        context.user_data['pending_action'] = f"delete_{data_split}"

    elif data == '1' or data == '2' or data == '3' or data == '4' or data == '5' or data == '6' or data == '7' or data == '8' or data == '9' or data == '10' or data == '11' or data == '12':
        context.user_data['month'] = data
        await context.bot.send_message(user_id, "Write a description:")
        context.user_data['pending_action'] = 'add_description'

    elif data == "exp&inc":
        year = datetime.datetime.now().year
        keyboard = [
            [
                InlineKeyboardButton(f"{year}", callback_data='this_year'),
            ],
            [
                InlineKeyboardButton("Another Year", callback_data='another_year')
            ],
            [
                InlineKeyboardButton("Back to Menu", callback_data='back_to_menu'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(user_id, text="Which year?", reply_markup=reply_markup)

    elif data == "this_year":
        year = datetime.datetime.now().year
        context.user_data['year'] = year
        keyboard = [
            [
                InlineKeyboardButton("1", callback_data='n_1'),
                InlineKeyboardButton("2", callback_data='n_2'),
                InlineKeyboardButton("3", callback_data='n_3'),
                InlineKeyboardButton("4", callback_data='n_4')
            ],
            [
                InlineKeyboardButton("5", callback_data='n_5'),
                InlineKeyboardButton("6", callback_data='n_6'),
                InlineKeyboardButton("7", callback_data='n_7'),
                InlineKeyboardButton("8", callback_data='n_8')
            ],
            [
                InlineKeyboardButton("9", callback_data='n_9'),
                InlineKeyboardButton("10", callback_data='n_10'),
                InlineKeyboardButton("11", callback_data='n_11'),
                InlineKeyboardButton("12", callback_data='n_12')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(user_id, text="Which month?", reply_markup=reply_markup)

    elif data == "another_year":
        await context.bot.send_message(user_id,
                                       text="Please enter the relevant year:\n\n(Use 4 digits - for example 2023)")
        context.user_data['pending_action'] = 'year_view'

    elif data == 'n_1' or data == 'n_2' or data == 'n_3' or data == 'n_4' or data == 'n_5' or data == 'n_6' or data == 'n_7' or data == 'n_8' or data == 'n_9' or data == 'n_10' or data == 'n_11' or data == 'n_12':
        month = data.split("_")[1]
        await display_exp_and_inc(user_id, month, context)


async def handle_user_input(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    user_input = update.message.text

    if 'pending_action' in context.user_data:
        pending_action = context.user_data['pending_action']

        if pending_action == 'first_time_name':
            context.user_data['first_name'] = user_input
            await context.bot.send_message(user_id, "What is your last name?")
            context.user_data['pending_action'] = 'first_time_last_name'

        elif pending_action == 'first_time_last_name':
            context.user_data['last_name'] = user_input
            keyboard = [
                [
                    InlineKeyboardButton("Yes", callback_data='yes_bank'),
                    InlineKeyboardButton("No", callback_data='no_bank')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(user_id,
                                           text="Would you like the bot to track your current bank account balance?",
                                           reply_markup=reply_markup)

        elif pending_action == 'first_time_bank':
            try:
                float_value = float(user_input)
                context.user_data['bank_account'] = float_value
                keyboard = [
                    [
                        InlineKeyboardButton("Yes", callback_data='yes_exp'),
                        InlineKeyboardButton("No", callback_data='no_exp')
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(user_id,
                                               text="Do you have expenses or income this month?",
                                               reply_markup=reply_markup)
            except ValueError:
                await context.bot.send_message(user_id,
                                               text="Oops! It looks like you entered something other than numbers. Please try again :)")
                await context.bot.send_message(user_id, text="Please enter your current bank account balance:")

        elif pending_action == 'first_time_exp':
            context.user_data['user_expenses'] = user_input
            await context.bot.send_message(user_id, text="Please provide your total income for this month:")
            context.user_data['pending_action'] = 'first_time_inc'

        elif pending_action == 'first_time_inc':
            context.user_data['user_income'] = user_input
            cursor.execute(
                'INSERT OR REPLACE INTO users (user_id, first_name, last_name, bank_account)'
                'VALUES (?, ?, ?, ?)',
                (
                    user_id,
                    context.user_data['first_name'],
                    context.user_data['last_name'],
                    None,
                ))
            conn.commit()

            if context.user_data['bank_account']:
                cursor.execute(f'UPDATE users SET bank_account = ? WHERE user_id = ?',
                               (context.user_data['bank_account'], user_id))
                conn.commit()

            cursor.execute(
                'INSERT OR REPLACE INTO expenses (user_id, category, month, description, amount)'
                'VALUES (?, ?, ?, ?, ?)',
                (
                    user_id,
                    'הוצאות נוספות',
                    datetime.datetime.now().month,
                    "month's total expenses",
                    context.user_data['user_expenses']
                ))
            conn.commit()

            cursor.execute(
                'INSERT OR REPLACE INTO income (user_id, category, month, description, amount)'
                'VALUES (?, ?, ?, ?, ?)',
                (
                    user_id,
                    'הכנסות נוספות',
                    datetime.datetime.now().month,
                    "month's total income",
                    context.user_data['user_income']
                ))
            conn.commit()

            await context.bot.send_message(user_id, text="We are done! Thank you for your cooperation")
            await display_main_menu(user_id, context)
            context.user_data.clear()

        elif pending_action.startswith('edit_settings_'):
            field = pending_action.split('_')[-1].replace(' ', '_')
            user_input = update.message.text
            user_id = update.message.chat_id

            cursor.execute(f'UPDATE users SET {field} = ? WHERE user_id = ?', (user_input, user_id))
            conn.commit()
            await context.bot.send_message(user_id,
                                           f"Details updated! \nTo view the changes, click on 'Balance Overview' in the Main Menu (/menu).")

            context.user_data.clear()

        elif pending_action == 'add_description':
            context.user_data['description'] = user_input
            await context.bot.send_message(user_id, text="Enter the amount:")
            context.user_data['pending_action'] = 'add_amount'

        elif pending_action == 'add_amount':
            try:
                float_value = float(user_input)
                context.user_data['amount'] = float_value
                category = context.user_data['category']
                exp_or_inc = category.split("_")[1]
                split_category = category.split("_")[0]
                if exp_or_inc == "הו":
                    cursor.execute('''
                                    INSERT OR REPLACE INTO expenses (user_id, category, month, year, description, amount)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                ''', (
                        user_id,
                        split_category,
                        context.user_data['month'],
                        datetime.datetime.now().year,
                        context.user_data['description'],
                        context.user_data['amount']
                    ))
                    conn.commit()
                else:
                    cursor.execute('''
                                    INSERT OR REPLACE INTO income (user_id, category, month, year, description, amount)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                ''', (
                        user_id,
                        split_category,
                        context.user_data['month'],
                        datetime.datetime.now().year,
                        context.user_data['description'],
                        context.user_data['amount']
                    ))
                    conn.commit()

                await context.bot.send_message(user_id,
                                               "Done!\n\nTo view your details, use the 'Expenses & Income' button in the Main Menu (/menu)")
                await manage_finances_command(user_id, context)
                context.user_data.clear()

            except ValueError:
                await context.bot.send_message(user_id,
                                               text="Oops! It looks like you entered something other than numbers. Please try again :)")
                await context.bot.send_message(user_id, text="Enter the amount:")

        elif pending_action == "income_entry" or pending_action == "expense_entry":
            entry = user_input
            temp = "inc"
            exp_or_inc = pending_action.split("_")[0]

            if exp_or_inc == "expense":
                exp_or_inc = "expenses"
                temp = "exp"

            cursor.execute(f'SELECT * FROM {exp_or_inc} WHERE user_id = ? AND {temp}_entry = ?', (user_id, entry))
            result = cursor.fetchone()
            if result is not None:
                context.user_data["entry"] = user_input
                pending_split = pending_action.split("_")[0]
                keyboard = [
                    [
                        InlineKeyboardButton("Category", callback_data=f'{pending_split}_Category')
                    ],
                    [
                        InlineKeyboardButton("Month", callback_data=f'{pending_split}_Month')
                    ],
                    [
                        InlineKeyboardButton("Year", callback_data=f'{pending_split}_Year')
                    ],
                    [
                        InlineKeyboardButton("Description", callback_data=f'{pending_split}_Description')
                    ],
                    [
                        InlineKeyboardButton("Amount", callback_data=f'{pending_split}_Amount')
                    ],
                    [
                        InlineKeyboardButton("Back to Menu", callback_data='back_to_manage')
                    ]

                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(user_id,
                                               text="Which field would you like to edit?",
                                               reply_markup=reply_markup)

            else:
                await context.bot.send_message(user_id,
                                               f"The specified entry is not found in your {exp_or_inc}. Please try again:")

        elif pending_action == "new_income_Month" or pending_action == "new_expense_Month" or pending_action == "new_income_Year" or pending_action == "new_expense_Year" or pending_action == "new_income_Description" or pending_action == "new_expense_Description" or pending_action == "new_income_Amount" or pending_action == "new_expense_Amount":
            exp_or_inc = pending_action.split("_")[1]
            split_category = pending_action.split("_")[2].lower()
            context.user_data[f"new_{split_category}"] = user_input

            if exp_or_inc == "income":
                cursor.execute(f'UPDATE income SET {split_category} = ? WHERE user_id = ? AND inc_entry = ?',
                               (context.user_data[f"new_{split_category}"], user_id, context.user_data['entry']))
                conn.commit()

            else:
                cursor.execute(f'UPDATE expenses SET {split_category} = ? WHERE user_id = ? AND exp_entry = ?',
                               (context.user_data[f"new_{split_category}"], user_id, context.user_data['entry']))
                conn.commit()

            await context.bot.send_message(user_id,
                                           "Done!\n\nTo view your details, use the 'Expenses & Income' button in the Main Menu (/menu)")
            await manage_finances_command(user_id, context)
            context.user_data.clear()

        elif pending_action == "delete_income" or pending_action == "delete_expense":
            entry = user_input
            temp = "inc"
            exp_or_inc = pending_action.split("_")[1]

            if exp_or_inc == "expense":
                exp_or_inc = "expenses"
                temp = "exp"

            cursor.execute(f'SELECT * FROM {exp_or_inc} WHERE user_id = ? AND {temp}_entry = ?', (user_id, entry))
            result = cursor.fetchone()
            if result is not None:
                cursor.execute(f'DELETE FROM {exp_or_inc} WHERE user_id = ? AND {temp}_entry = ?', (user_id, entry))
                conn.commit()
                await context.bot.send_message(user_id,
                                               "Done!\n\nTo view your details, use the 'Expenses & Income' button in the Main Menu (/menu)")
                await manage_finances_command(user_id, context)
            else:
                await context.bot.send_message(user_id,
                                               f"The specified entry is not found in your {exp_or_inc}. Please try again:")

        elif pending_action == 'year_view':
            if user_input.isdigit() and (len(user_input) == 4):
                context.user_data['year'] = user_input
                keyboard = [
                    [
                        InlineKeyboardButton("1", callback_data='n_1'),
                        InlineKeyboardButton("2", callback_data='n_2'),
                        InlineKeyboardButton("3", callback_data='n_3'),
                        InlineKeyboardButton("4", callback_data='n_4')
                    ],
                    [
                        InlineKeyboardButton("5", callback_data='n_5'),
                        InlineKeyboardButton("6", callback_data='n_6'),
                        InlineKeyboardButton("7", callback_data='n_7'),
                        InlineKeyboardButton("8", callback_data='n_8')
                    ],
                    [
                        InlineKeyboardButton("9", callback_data='n_9'),
                        InlineKeyboardButton("10", callback_data='n_10'),
                        InlineKeyboardButton("11", callback_data='n_11'),
                        InlineKeyboardButton("12", callback_data='n_12')
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(user_id, text="Which month?", reply_markup=reply_markup)
            else:
                await context.bot.send_message(user_id,
                                               text="Oops! It looks like you entered an incorrect value. Please try again :)")
                await context.bot.send_message(user_id,
                                               text="Please enter the relevant year:\n\n(Use 4 digits - for example 2023)")

    else:
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if not result:
            await context.bot.send_message(user_id,
                                           text="Hello! \nAccording to the information I have, it seems you haven't created a profile yet. \nTo get started, please press /start")


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'update {update} caused error {context.error}')


if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('menu', menu_command))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))

    # Error
    app.add_error_handler(error)

    # Polls the bot
    print('Polling...')
    app.run_polling(poll_interval=3)
