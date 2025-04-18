from flask import Flask, render_template, request, send_file, jsonify
import os
import subprocess
import tempfile
import shutil
import uuid

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    try:
        # Get data from request
        data = request.json
        name = data.get('name', '')
        reg_number = data.get('regNumber', '')
        teacher_name = data.get('teacherName', '')
        pronoun = data.get('pronoun', '')

        # Generate LaTeX code with the form values
        latex_code = generate_latex_code(name, reg_number, teacher_name,
                                         pronoun)

        # Create a unique temporary directory
        temp_dir = os.path.join("tmp", str(uuid.uuid4()))
        os.makedirs(temp_dir, exist_ok=True)

        # Create the tex file
        tex_file_path = os.path.join(temp_dir, 'document.tex')
        with open(tex_file_path, 'w', encoding='utf-8') as f:
            f.write(latex_code)

        # Copy logo file to temp directory
        logo_path = os.path.join(os.path.dirname(__file__), 'static',
                                 'Logo.png')
        font_path = os.path.join(os.path.dirname(__file__), 'fonts',
                                 'TimesNewRoman.ttf')
        shutil.copy(logo_path, os.path.join(temp_dir, 'Logo.png'))
        os.makedirs(os.path.join(temp_dir, 'fonts'), exist_ok=True)
        shutil.copy(font_path,
                    os.path.join(temp_dir, 'fonts', 'TimesNewRoman.ttf'))
        # Run lualatex
        process = process = subprocess.Popen(
            ['lualatex', '--interaction=nonstopmode', 'document.tex'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=temp_dir)
        stdout, stderr = process.communicate()
        print(stdout.decode('utf-8'))
        print(stderr.decode('utf-8'))

        if process.returncode != 0:
            return jsonify({
                'success':
                False,
                'error':
                f'LaTeX compilation failed: {stderr.decode("utf-8")}'
            }), 500

        # Path to the generated PDF
        pdf_path = os.path.join(temp_dir, 'document.pdf')

        if not os.path.exists(pdf_path):
            return jsonify({
                'success': False,
                'error': 'PDF was not generated'
            }), 500

        # Save PDF to a location where it can be served
        output_dir = os.path.join(os.path.dirname(__file__), 'static', 'pdfs')
        os.makedirs(output_dir, exist_ok=True)

        # Use a unique name for the PDF
        pdf_filename = f"{uuid.uuid4()}.pdf"
        output_pdf_path = os.path.join(output_dir, pdf_filename)
        shutil.copy(pdf_path, output_pdf_path)

        # Clean up temp directory
        os.system(f'rm -rfv "{temp_dir}"')

        return jsonify({
            'success': True,
            'pdf_url': f'/static/pdfs/{pdf_filename}'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def generate_latex_code(name, roll_no, teacher, pronoun):
    # Get current date
    from datetime import datetime
    current_date = "April, 2025"  #datetime.now().strftime('%B, %Y')
    honorifics = "Mr." if pronoun == "him" else "Ms." if pronoun == "her" else "Mx."
    # LaTeX template with variables replaced
    return f'''\\documentclass[12pt]{{article}}
\\usepackage{{amsmath}}
\\usepackage{{geometry}}
\\usepackage{{setspace}}
\\usepackage{{fancyhdr}}
\\usepackage{{graphicx}}
\\usepackage{{array}}
\\usepackage{{booktabs}}
\\usepackage{{fontspec}}
\\usepackage{{titlesec}}
\\usepackage[T1]{{fontenc}}
%Document Setup:
\\newcommand{{\\Name}}{{{name} }}
\\newcommand{{\\RollNo}}{{{roll_no} }}
\\newcommand{{\\Date}}{{{current_date} }}
\\newcommand{{\\Pronoun}}{{{pronoun} }}
\\newcommand{{\\honorifics}}{{{honorifics} }}
\\newcommand{{\\Teacher}}{{{teacher} }}
\\newcommand{{\\Title}}{{Experimental Psychology Practical Report}}
\\newcommand{{\\TitleShort}}{{Experimental Psychology}}
%aAPA
\\geometry{{left=1in, right=1in, top=1in, bottom=1in}}
\\setlength{{\\parindent}}{{0.5in}}
\\doublespacing
\\setmainfont{{Times New Roman}}[
    Path = ./fonts/,
    Extension = .ttf,
    UprightFont = *
]
\\titleformat{{\\subsubsection}}
  {{\\normalfont\\normalsize\\bfseries\\itshape}}{{\\thesubsubsection}}{{1em}}{{}}
\\pagestyle{{fancy}}
\\fancyhf{{}}
\\fancyhead[L]{{\\TitleShort}}  
\\fancyhead[R]{{\\thepage}}
\\begin{{document}}
\\begin{{titlepage}}
    \\centering
    \\vskip 1in
    \\includegraphics[width=0.75\\textwidth]{{Logo.png}} \\\\
    \\vskip 0.5in
    {{\\Large \\bfseries \\Title}}
    \\vskip 0.5cm
    {{By \\\\ \\Name \\\\ \\RollNo \\\\ 2 BPSY NCR A  \\\\ Bachelor of Science \\\\ Psychology (Honours/Honours with Research) \\\\ Department of Psychology \\\\ Christ (Deemed to be University), NCR}}
    \\vskip 0.5in
    {{\\textbf{{Experimental Psychology-II (BPSY411-2)}} \\\\ Under the Supervision of \\\\ \\Teacher \\\\ \\Date}}
\\end{{titlepage}}
    \\thispagestyle{{fancy}}
\\newpage
\\begin{{titlepage}}
    \\begin{{center}}
        {{\\Large \\bfseries Certificate}}
    \\end{{center}}
    \\vskip 0.5cm
    {{This is to certify that this practical report submitted by \\honorifics \\Name ( \\RollNo) is a record of the practical work completed for the course titled Experimental Psychology (BPSY411-2), by \\Pronoun during the academic year 2024-2025 under my supervision in partial fulfillment for the award of BSc.Psychology (Honours/Honours with research) degree.}}
    \\vskip 0.5in
    {{\\noindent\\textbf{{Place:}} Delhi NCR \\\\ \\textbf{{Date:}} \\Date}}
    \\vskip 0.5in
    \\begin{{flushleft}}
    \\begin{{tabular}}{{>{{\\raggedright\\arraybackslash}}p{{10cm}} p{{10cm}}}}
        \\rule{{0.7\\linewidth}}{{0.4pt}} & \\rule{{0.7\\linewidth}}{{0.4pt}} \\\\
        \\textbf{{Batch Supervisor Signature}} & \\textbf{{ Dr. Ridhima Shukla}} \\\\
        Department of Psychology & Head of Department \\\\
        School of Social Sciences  & Department of Psychology \\\\
        CHRIST (Deemed to be University) & School of Social Sciences \\\\
        Delhi - NCR & CHRIST (Deemed to be University) \\\\
        & Delhi - NCR \\\\
    \\end{{tabular}}
\\end{{flushleft}}
\\vskip 0.5in
\\end{{titlepage}}
\\newpage
\\begin{{titlepage}}
    \\begin{{center}}
        {{\\Large \\bfseries Declaration}}
    \\end{{center}}
    \\vskip 0.5cm
    {{I, \\Name with Reg No. \\RollNo hereby declare that this record of practical work is original and was completely under the supervision of \\Teacher for the course Experimental Psychology (BPSY411-2) in partial fulfilment for the award of BSc.Psychology (Honours/Honours with research) degree.}}
    \\vskip 0.5in
    {{\\noindent\\textbf{{Place:}} Delhi NCR \\\\ \\textbf{{Date:}} \\Date}}
    \\vskip 0.5in
    \\begin{{flushright}}
    \\noindent\\rule{{0.4\\linewidth}}{{0.4pt}} \\\\ \\Name \\\\ Register no. \\RollNo \\\\ Department of Psychology \\\\ School of Social Sciences \\\\ CHRIST (Deemed to be University) \\\\ Delhi - NCR
    \\end{{flushright}}
\\end{{titlepage}}
\\end{{document}}'''


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
