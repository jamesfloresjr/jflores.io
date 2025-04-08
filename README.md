# Personal Portfolio Website

A modern, responsive portfolio website built with Flask, featuring a clean design with dark/light mode support.

## Features

- Responsive design that works on all devices
- Modern UI with smooth animations
- Dark/light mode toggle with system preference detection
- Sections for:
  - Home/Introduction
  - Resume/Experience
  - Projects showcase
  - Contact form
  - Skills and certifications

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
.\venv\Scripts\activate
```
- Unix/MacOS:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to `http://localhost:5000`

## Customization

1. Update the content in the template files:
   - `templates/index.html`
   - `templates/resume.html`
   - `templates/projects.html`
   - `templates/contact.html`

2. Modify the styling in `static/css/style.css`

3. Add your own images and assets to the `static` directory

## Project Structure

```
portfolio/
├── app.py              # Flask application
├── requirements.txt    # Python dependencies
├── static/
│   └── css/
│       └── style.css  # Stylesheets
└── templates/
    ├── base.html      # Base template
    ├── index.html     # Home page
    ├── resume.html    # Resume page
    ├── projects.html  # Projects page
    └── contact.html   # Contact page
```

## License

This project is open source and available under the MIT License. 