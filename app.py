from fastapi import FastAPI
import requests

app = FastAPI()

OLLAMA_URL = "http://localhost:11434/api/generate"

@app.post("/ask")
def ask(query: str):
    payload = {
        "model": "mistral",
        "prompt": """Here is my framework doc:\n\nTableRF TableRF: A Streamlined Component for Web Applications TableRF is a streamlined and user-friendly component within the RapidFire UI framework, specifically designed for creating tables in web applications. It offers an efficient and intuitive way to display tabular data, making it an essential tool for developers who need to present information in a clear, organized, and visually appealing format.

Key Features and Advantages of TableRF

Simplified Table Creation

Concise Syntax: TableRF simplifies the table creation process with a straightforward and intuitive syntax. This reduces the amount of code required, allowing developers to quickly build tables without complex HTML or CSS. This feature is particularly useful in fast-paced development environments or when multiple tables are needed.
Predefined Structures: TableRF includes predefined structures and styles, enabling developers to create fully functional tables with minimal configuration. These elements help standardize table creation across applications, ensuring consistency and saving development time.
User-Friendly Design

Ease of Use: TableRF is built to be intuitive, making it easy for both experienced developers and newcomers to create and manage tables. The component handles much of the complexity behind the scenes, allowing developers to focus on data rather than layout.
Accessibility: TableRF ensures that tables are accessible to all users, including those with disabilities. It supports features like keyboard navigation and screen reader compatibility, making tables more inclusive and improving the overall user experience.
Customization and Flexibility

Customizable Appearance: While TableRF provides a default style, it also offers flexibility for customization. Developers can adjust the appearance, including colors, fonts, borders, and spacing, to match the web application’s design.
Dynamic Content Handling: TableRF is designed to handle dynamic content efficiently, making it ideal for applications that require frequent updates or that display large datasets.
Enhanced Functionality

Sorting and Filtering: TableRF often includes built-in features like column sorting and data filtering. These features allow users to interact with the table by sorting data or filtering rows based on specific criteria without additional code or plugins.
Pagination: For tables with a large number of entries, TableRF can automatically handle pagination, breaking the data into manageable chunks and providing easy navigation through content. This improves performance and keeps the interface clean.
Responsive Design

Automatic Adjustment: TableRF is built to be responsive, automatically adjusting the layout based on the device's screen size. On smaller screens, the table might switch to a more mobile-friendly format, such as stacking columns vertically or providing a scrollable interface.
Custom Breakpoints: Developers can define custom breakpoints to control how and when the table layout should change, offering greater flexibility in creating responsive designs.
Integration with Other Components

Seamless Component Integration: TableRF integrates smoothly with other RapidFire components, such as buttons, forms, and modal dialogs. For example, developers can easily add interactive elements like edit buttons or detail views within the table.
Data Binding: TableRF supports easy data binding, allowing developers to connect the table directly to data sources like databases or APIs. This ensures that the table content is always up-to-date.
Performance Optimization

Efficient Rendering: TableRF is optimized for performance, ensuring that even large tables render quickly and efficiently. This is crucial for data-heavy applications.
Lightweight and Fast: Despite its powerful features, TableRF is designed to be lightweight, minimizing its impact on page load times and ensuring a smooth user experience.
Practical Application

Consider a business dashboard that needs to display sales data for different products. Using TableRF, a developer can quickly create a responsive and interactive table listing all products, their sales figures, and other relevant data. Users can sort the table by various columns and filter data to focus on specific categories. If the table contains too many entries, pagination will automatically be applied, making navigation easier.

Summary

TableRF is a powerful, user-friendly tool for creating tables in web applications. Its concise syntax, customization options, and responsive design capabilities make it ideal for developers who need to present data in a clear, organized, and interactive format. Whether for simple data tables or complex, dynamic datasets, TableRF enhances the functionality and aesthetic appeal of web applications, making it a vital component of the RapidFire UI framework.\n\nNow answer: What is TableRF and how does it work?""",
        "stream": False
    }
    response = requests.post(OLLAMA_URL, json=payload)
    return response.json()
