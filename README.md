# EAGL: Evolution-Aware Generation of Robust Locators

EAGL (Evolution-Aware Generation of Robust Locators): A novel technique for generating robust locators by analysing the evolution of web applications. EAGL identifies stable DOM positions—specific locations in the DOM tree that persist across versions—using six structural DOM features, and uses them as anchors to construct robust locators.


## Getting Started

### Prerequisites

- Python 3.8+
- Required Python packages (see `requirements.txt`)

### Installation

Clone the repository:
```sh
git clone https://github.com/yourusername/EAGL.git
cd EAGL
```

Install the Requirements from the file

```sh
pip install -r requirements.txt 
```

You can also use the virtual enviroment in the repository

```sh
cd EAGL
.\venv\Scripts\activate
```

### Usage

Run the main executor script which will select a random element from the HTML page, generate and print the locator and the time it took to generate the locator:
```sh
python EAGL_excutor.py
```
