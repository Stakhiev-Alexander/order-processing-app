import sqlite3
from reportlab.lib import colors
from reportlab.lib import pagesizes
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont 
from reportlab.platypus import Table, TableStyle


class const:
    INPUT_FILE_NAME = 'in.txt'
    OUTPUT_FILE_NAME = 'output.pdf'
    DB_NAME = 'prices.db'


def parse_input(input_file_name):
    products_names = []
    products_quantity = []
    with open(input_file_name, "r") as f:
        for line in f:
            parse_unit = line.split()
            while '-' in parse_unit: parse_unit.remove('-')
            while '–' in parse_unit: parse_unit.remove('–')
            while '.' in parse_unit: parse_unit.remove('.')
            while ',' in parse_unit: parse_unit.remove(',')
            for i in range (len(parse_unit)):
                if (parse_unit[i] == 'шт' or parse_unit[i] == 'шт.'):
                    tmp_quantity = parse_unit[i - 1]
                    tmp_name = parse_unit
                    tmp_name.pop()
                    tmp_name.pop()

                    products_quantity.append(tmp_quantity)
                    products_names.append(' '.join(str(x) for x in tmp_name)) 

    return  products_names, products_quantity                         
    

def products_price_db(db_name, products_names):
    products_prices = []
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        for i in range(len(products_names)):
            sql = f"SELECT price FROM prices WHERE name LIKE '{products_names[i]}'"
            cursor.execute(sql)
            products_prices.append(cursor.fetchone()[0])
    return products_prices    


def construct_pdf(output_file_name, products_names, products_quantity, products_price):
    if (len(products_names) != len(products_quantity) or len(products_names) != len(products_price)):
        return 

    number_of_products = len(products_names) 
    c = canvas.Canvas(output_file_name)

    # Page sizes
    width, height = pagesizes.A4

    # Header text
    pdfmetrics.registerFont(TTFont('Verdana', 'Verdana.ttf'))
    c.setFont("Verdana", 12)
    s = u"Информация"
    c.drawString(10, height - 15, s)
    s = u"о заказе:"
    c.drawString(10, height - 30, s)

    c.setFont("Verdana", 20)
    s = u"ИНФОРМАЦИЯ О ЗАКАЗЕ"
    c.drawRightString(width - 10, height - 30 , s)
    c.line(10, height - 40, width - 10, height - 40)


    # Drawing table
    ## Table headers
    h0 = u"Товар"
    h1 = u"К-во"
    h2 = u"Цена за ед."
    h3 = u"Сумма"
    data = [[h0, h1, h2, h3]]

    h2_phrase_ending = u" руб. /шт"
    h3_phrase_ending = u" руб."
    total_sum = 0
    max_lines_in_cell = 0
    
    for i in range(number_of_products):
        # Make sure the strings fit in table
        lst = products_names[i].split()
        for j in range(3, len(lst), 3):
            lst.insert(j, '\n')     
        lines_in_cell = lst.count('\n') + 1   
        products_names[i] = ' '.join(str(x) for x in lst) 

        # Counting total sum for all products
        total_sum += int(products_price[i])*int(products_quantity[i])

        data.append([products_names[i], products_quantity[i], str(products_price[i]) + h2_phrase_ending,
         str(int(products_price[i])*int(products_quantity[i])) + h3_phrase_ending])

        if max_lines_in_cell < lines_in_cell: max_lines_in_cell = lines_in_cell

    t = Table(data, colWidths = 100, rowHeights = max_lines_in_cell * 12.5)
    t.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,0), colors.grey),
                            ('ALIGN', (0,0), (-1,0), 'CENTER'),
                            ('VALIGN', (0,0), (-1,-1), 'TOP'),
                            ('FONTNAME', (0,0), (-1, -1), "Verdana"),
                            ('FONTSIZE', (0,0), (-1, -1), 8),
                            ('LINEABOVE', (0,1), (-1,1), 1, colors.black),
                            ('LINEABOVE', (0,2), (-1,-1), 0.25, colors.black),
                            ('LINEBEFORE', (0,0), (-1,-1), 0.25, colors.black),
                            ('BOX', (0,0), (-1,-1), 0.25, colors.black)
                          ]
    ))

    t._argW[0] = width - 320
    table_height = (number_of_products + 1) * (max_lines_in_cell * 12.5)

    t.wrapOn(c, width, height)
    t.drawOn(c, 10, height - 60 - table_height) 

    # Bottom text
    c.setFont("Verdana", 12)

    longest_string = str(round(total_sum * 1.2, 2)) + h3_phrase_ending

    s1 = u"Сумма: "
    s2 = str(round(total_sum, 2)) + h3_phrase_ending 
    c.drawRightString(width - 10, height - 80 - table_height, s2)
    c.drawRightString(width - 150 - len(longest_string), height - 80 - table_height, s1)

    s1 = u"НДС 20%: "
    s2 = str(round(total_sum * 0.2, 2)) + h3_phrase_ending
    c.drawRightString(width - 10, height - 100 - table_height, s2)
    c.drawRightString(width - 150 - len(longest_string), height - 100 - table_height, s1) 

    s1 = u"Итоговая сумма: "
    s2 = str(round(total_sum * 1.2, 2)) + h3_phrase_ending
    c.drawRightString(width - 10, height - 140 - table_height, s2)
    c.drawRightString(width - 150 - len(longest_string), height - 140 - table_height, s1)

    c.line(width - 10, height - 120 - table_height, width - len(longest_string) - 220, height - 120 - table_height)

    c.showPage()
    c.save()


def main():
    products_names, products_quantity = parse_input(const.INPUT_FILE_NAME)
    products_prices = products_price_db(const.DB_NAME, products_names)

    prices_valid = True

    for i in range(len(products_prices)):
        if type(products_prices[i]) == type(None):
            prices_valid = False

    if prices_valid: construct_pdf(const.OUTPUT_FILE_NAME, products_names, products_quantity, products_prices)
    else:  print("Some prices not found")


if __name__ == "__main__":
    main()
