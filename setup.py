from setuptools import setup, find_packages

setup(
    name="train_offer_by_station_fr", 
    version="1.0.0",  
    description="A package to analyze train offers by station in France", 
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Jules Crouzet",  # Nom de l'auteur
    packages=find_packages(where="src"),
    package_dir={"": "src"},  # Répertoire source des packages
    include_package_data=True,
    install_requires=[
        "altair>=5.4.1",
        "emoji>=2.14.0",
        "folium>=0.17.0",
        "matplotlib>=3.9.2",
        "numpy>=2.1.3",
        "pandas>=2.2.3",
        "pytz>=2024.2",
        "requests>=2.32.3",
        "setuptools>=75.3.0",
        "streamlit>=1.39.0",
        "streamlit_folium>=0.23.1",
    ],

    python_requires=">=3.12",
)
