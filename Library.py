# app.py
import streamlit as st
import requests
import pandas as pd
from typing import List, Dict, Any

st.set_page_config("Buscador de Novelas Web", page_icon="📚", layout="wide")
st.title("📚 Buscador de novelas web — prototipo educativo")
st.markdown(
    "Busca libros/novelas por título, autor o género. Usa Open Library (sin clave) y opcionalmente Google Books (requiere API key)."
)
st.write("⚠️ Este prototipo devuelve metadatos y enlaces a fuentes públicas; no sirve para obtener contenido con copyright de forma ilegal.")

# ----- Helpers -----
OPENLIB_SEARCH_URL = "https://openlibrary.org/search.json"
OPENLIB_WORK_URL = "https://openlibrary.org{key}"
GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"

def search_openlibrary(q: str, subject: str = "", limit: int = 20) -> List[Dict[str,Any]]:
    params = {"q": q, "limit": limit}
    if subject:
        # OpenLibrary supports subject: search using "subject:fantasy" in q
        params["q"] = f"{q} subject:{subject}"
    r = requests.get(OPENLIB_SEARCH_URL, params=params, timeout=10)
    if r.status_code != 200:
        return []
    data = r.json()
    results = []
    for doc in data.get("docs", []):
        # prefer work key and title/author
        work_key = doc.get("key")  # e.g. /works/OLxxxxxW
        title = doc.get("title")
        authors = doc.get("author_name") or []
        cover_id = doc.get("cover_i")
        first_publish = doc.get("first_publish_year")
        subjects = doc.get("subject") or []
        results.append({
            "source": "OpenLibrary",
            "title": title,
            "authors": ", ".join(authors),
            "work_key": work_key,
            "open_url": f"https://openlibrary.org{work_key}" if work_key else "",
            "cover_id": cover_id,
            "first_publish_year": first_publish,
            "subjects": subjects
        })
    return results

def openlibrary_cover_url(cover_id:int, size:str="M") -> str:
    # size: S, M, L
    if not cover_id:
        return ""
    return f"https://covers.openlibrary.org/b/id/{cover_id}-{size}.jpg"

def search_google_books(q: str, api_key: str = None, limit: int = 20) -> List[Dict[str,Any]]:
    params = {"q": q, "maxResults": min(limit, 40)}
    if api_key:
        params["key"] = api_key
    r = requests.get(GOOGLE_BOOKS_URL, params=params, timeout=10)
    if r.status_code != 200:
        return []
    data = r.json()
    items = data.get("items", [])[:limit]
    results = []
    for item in items:
        info = item.get("volumeInfo", {})
        title = info.get("title")
        authors = info.get("authors", [])
        published = info.get("publishedDate")
        description = info.get("description", "")
        info_link = info.get("infoLink", "")
        thumbnail = info.get("imageLinks", {}).get("thumbnail", "")
        categories = info.get("categories", [])
        results.append({
            "source": "GoogleBooks",
            "title": title,
            "authors": ", ".join(authors),
            "published": published,
            "description": description,
            "info_link": info_link,
            "thumbnail": thumbnail,
            "categories": categories
        })
    return results

# ----- UI: filtros y búsqueda -----
with st.sidebar:
    st.header("Filtros y configuración")
    query = st.text_input("Buscar (título, autor, palabra clave):", "")
    genre = st.selectbox("Género (novelas web):", [
        "", "fantasía", "isekai", "romance", "litRPG", "ciencia ficción",
        "wuxia", "cultivo", "thriller", "misterio", "horror",
        "slice of life", "histórico", "drama", "aventura", "comedia"
    ])
    language = st.selectbox("Idioma (filtro):", ["", "en", "es", "zh", "ja", "ko", "pt", "fr"])
    source_openlib = st.checkbox("Buscar en Open Library (gratuito)", value=True)
    source_google = st.checkbox("Buscar en Google Books (opcional)", value=False)
    google_key = st.text_input("Google Books API Key (opcional):", "")
    limit = st.slider("Resultados por fuente:", 5, 40, 15)
    st.markdown("---")
    st.write("Nota: la búsqueda de género usa palabras clave; algunos géneros 'web novel' no están explícitos en todas las APIs.")

# Si no hay query, muestra ayuda
if not query:
    st.info("Escribe un término de búsqueda (título, autor o tema) y presiona Buscar.")
    st.stop()

# Ejecutar búsquedas
results = []
if source_openlib:
    q_ol = query
    subj = genre if genre else ""
    if language:
        # OpenLibrary doesn't have a single param for language in search.json; we can include "language:eng" in q
        # but language codes in OL: eng, spa, etc. mapping not implemented here; we include language as keyword for best effort.
        q_ol = f"{q_ol} language:{language}"
    try:
        ol = search_openlibrary(q_ol, subject=subj, limit=limit)
        results.extend(ol)
    except Exception as e:
        st.warning(f"OpenLibrary error: {e}")

if source_google:
    q_gb = query
    if genre:
        q_gb = f"{q_gb} {genre}"
    if language:
        q_gb = f"{q_gb} language:{language}"
    try:
        gb = search_google_books(q_gb, api_key=google_key or None, limit=limit)
        results.extend(gb)
    except Exception as e:
        st.warning(f"Google Books error: {e}")

# ----- Mostrar resultados -----
st.header(f"Resultados (~{len(results)} encontrados)")
if not results:
    st.info("No se encontraron resultados. Prueba con otros términos o quita filtros.")
    st.stop()

# Convert to DataFrame for easy display (normalize keys)
rows = []
for r in results:
    if r["source"] == "OpenLibrary":
        rows.append({
            "Fuente": r["source"],
            "Título": r.get("title",""),
            "Autor(es)": r.get("authors",""),
            "Año": r.get("first_publish_year",""),
            "Enlace": r.get("open_url",""),
            "Portada": openlibrary_cover_url(r.get("cover_id"))
        })
    else:
        rows.append({
            "Fuente": r["source"],
            "Título": r.get("title",""),
            "Autor(es)": r.get("authors",""),
            "Año": r.get("published",""),
            "Enlace": r.get("info_link",""),
            "Portada": r.get("thumbnail","")
        })

df = pd.DataFrame(rows)

# Mostrar lista con tarjetas
for i, row in df.iterrows():
    cols = st.columns([1,4])
    with cols[0]:
        if row["Portada"]:
            st.image(row["Portada"], width=120)
        else:
            st.write("📘")
    with cols[1]:
        st.markdown(f"### {row['Título']}")
        st.write(f"**Fuente:** {row['Fuente']}   •   **Autor(es):** {row['Autor(es)']}")
        if row["Año"]:
            st.write(f"**Año:** {row['Año']}")
        if row["Enlace"]:
            st.markdown(f"[Ver en fuente]({row['Enlace']})")
        st.divider()
