# app.py
import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime
from urllib.parse import quote_plus

st.set_page_config("Biblioteca de Novelas Web (gratis y legales)", page_icon="📚", layout="wide")
st.title("📚 Buscador y Biblioteca — libros gratis y legales (prototipo)")

st.markdown(
    """
    **Qué hace esta app:** busca libros de dominio público (o disponibles públicamente) y te permite leer en la app,
    descargar (si el archivo está disponible) y guardar títulos en tu **biblioteca personal**.
    """
)
st.info("⚠️ Uso educativo: verifica siempre la licencia en la fuente antes de descargar o redistribuir.")

# --- Rutas / archivos locales para almacenamiento simple ---
LIBRARY_CSV = "library.csv"   # guardará las entradas de la biblioteca personal
if not os.path.exists(LIBRARY_CSV):
    pd.DataFrame(columns=["nickname","book_id","title","authors","source","download_url","saved_at"]).to_csv(LIBRARY_CSV, index=False)

# ------------------------------
#  Fuentes: Gutendex (Gutenberg) y Open Library
# ------------------------------
GUTENDEX_SEARCH = "https://gutendex.com/books"
OPENLIB_SEARCH = "https://openlibrary.org/search.json"

# Helpers
def search_gutendex(q, page_size=20):
    try:
        params = {"search": q, "topic": "", "mime_type": "", "page_size": page_size}
        r = requests.get(GUTENDEX_SEARCH, params={"search": q, "page_size": page_size}, timeout=12)
        r.raise_for_status()
        data = r.json()
        results = []
        for item in data.get("results", []):
            # formats: many keys with mime types and urls
            results.append({
                "source": "Gutenberg",
                "id": f"gutenberg_{item.get('id')}",
                "title": item.get("title"),
                "authors": ", ".join([a.get("name","") for a in item.get("authors",[])]),
                "formats": item.get("formats", {}),
                "download_url": guess_best_download_url(item.get("formats", {})),
                "info_url": f"https://gutendex.com/books/{item.get('id')}"
            })
        return results
    except Exception as e:
        st.warning(f"Error Gutendex: {e}")
        return []

def search_openlibrary(q, page_size=20):
    try:
        # usar q directamente; Open Library devuelve muchos items
        r = requests.get(OPENLIB_SEARCH, params={"q": q, "limit": page_size}, timeout=12)
        r.raise_for_status()
        data = r.json()
        results = []
        for doc in data.get("docs", []):
            work_key = doc.get("key")  # /works/OL...
            title = doc.get("title")
            authors = doc.get("author_name") or []
            # OpenLibrary tiene "ia" identifiers que a veces enlazan a Internet Archive
            ia = doc.get("ia") or []
            # construir un posible pdf/epub link via OpenLibrary page
            open_url = f"https://openlibrary.org{work_key}" if work_key else ""
            results.append({
                "source": "OpenLibrary",
                "id": f"openlib_{doc.get('key','')}",
                "title": title,
                "authors": ", ".join(authors),
                "formats": {},  # no list directly here
                "download_url": open_url,
                "info_url": open_url
            })
        return results
    except Exception as e:
        st.warning(f"Error OpenLibrary: {e}")
        return []

def guess_best_download_url(formats: dict):
    """
    formats: dict returned by Gutendex with keys like:
    'text/plain; charset=utf-8', 'application/epub+zip', 'text/html; charset=utf-8', etc.
    Priorizar: epub > text/plain > text/html > mobi
    """
    prefer = ["application/epub+zip", "text/plain; charset=utf-8", "text/html; charset=utf-8", "application/x-mobipocket-ebook"]
    for p in prefer:
        if p in formats:
            return formats[p]
    # fallback: any url
    for v in formats.values():
        if isinstance(v, str) and v.startswith("http"):
            return v
    return ""

# ------------------------------
#  UI: búsqueda
# ------------------------------
with st.sidebar:
    st.header("Buscar libros (gratuitos/legal)")
    query = st.text_input("Título, autor o palabra clave:")
    source_gut = st.checkbox("Gutenberg (Gutendex)", value=True)
    source_ol = st.checkbox("Open Library", value=True)
    max_results = st.slider("Resultados por fuente:", 5, 40, 15)
    st.markdown("---")
    st.subheader("Tu biblioteca")
    nickname = st.text_input("Nombre para tu biblioteca (ej: 'Sistine'):", value="Visitante")
    st.write("Tu biblioteca se guarda por *nickname* en el archivo `library.csv` (persistencia limitada).")
    st.button("Refrescar app")  # forzar rerun si se desea

if not query:
    st.info("Escribe un término de búsqueda en la barra lateral para empezar.")
    st.stop()

# Ejecutar búsquedas
results = []
if source_gut:
    results += search_gutendex(query, page_size=max_results)
if source_ol:
    results += search_openlibrary(query, page_size=max_results)

st.write(f"🔎 Resultados aproximados: **{len(results)}**")

# Mostrar resultados con tarjetas
for idx, book in enumerate(results):
    cols = st.columns([1,5,2])
    with cols[0]:
        # mostrar icono o thumbnail si es posible (Gutendex no siempre devuelve cover url)
        if book["source"] == "Gutenberg" and book["formats"].get("image/jpeg"):
            st.image(book["formats"].get("image/jpeg"), width=100)
        else:
            st.write("📘")
    with cols[1]:
        st.markdown(f"### {book['title']}")
        st.write(f"**Fuente:** {book['source']} — **Autor(es):** {book.get('authors','')}")
        st.write(f"[Ver detalles]({book.get('info_url')})")
    with cols[2]:
        # Botones: Leer, Descargar (si hay url), Guardar
        can_download = bool(book.get("download_url"))
        # Leer en app (intentar abrir txt/html)
        if st.button(f"Leer ▶ (#{idx})"):
            # intentar obtener texto y mostrar en modal/expander
            url = book.get("download_url") or book.get("info_url")
            if not url:
                st.warning("No hay URL de lectura directa; abre la página de la fuente.")
            else:
                try:
                    r = requests.get(url, timeout=15)
                    r.raise_for_status()
                    content_type = r.headers.get("Content-Type","")
                    text = r.text
                    # Mostrar en expander grande
                    st.session_state["last_read_title"] = book["title"]
                    st.session_state["last_read_text"] = text
                    st.session_state["last_read_source"] = book["source"]
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"No fue posible obtener el texto: {e}")
        if can_download:
            st.markdown(f"[Descargar archivo]({book['download_url']})")
        else:
            st.write("🔒 Descarga no disponible")
        if st.button(f"Guardar ⭐ (#{idx})"):
            # guardar en library.csv
            df_lib = pd.read_csv(LIBRARY_CSV, dtype=str)
            entry = {
                "nickname": nickname,
                "book_id": book["id"],
                "title": book["title"],
                "authors": book.get("authors",""),
                "source": book["source"],
                "download_url": book.get("download_url") or book.get("info_url"),
                "saved_at": datetime.utcnow().isoformat()
            }
            df_lib = pd.concat([df_lib, pd.DataFrame([entry])], ignore_index=True)
            df_lib.to_csv(LIBRARY_CSV, index=False)
            st.success(f"Guardado en la biblioteca de '{nickname}'")

# ------------------------------
#  Mostrar texto leído (si existe)
# ------------------------------
if st.session_state.get("last_read_text"):
    st.markdown("---")
    st.subheader(f"Leyendo: {st.session_state.get('last_read_title')} — Fuente: {st.session_state.get('last_read_source')}")
    text = st.session_state.get("last_read_text", "")
    st.warning("El texto completo puede ser muy grande — la visualización aquí es para lectura rápida. Para descargar usa el enlace de descarga cuando exista.")
    # mostrar en un expander con scroll
    with st.expander("Abrir lector (texto completo)", expanded=True):
        # para evitar bloquear UI con textos enormes, limitar a 50000 caracteres a la vez
        max_chars = 200000
        if len(text) > max_chars:
            st.text_area("Contenido (vista parcial)", value=text[:max_chars] + "\n\n[...texto truncado por límite de vista...]", height=600)
            st.info("El texto ha sido truncado para una visualización cómoda. Usa el enlace de descarga para obtener el archivo completo.")
        else:
            st.text_area("Contenido", value=text, height=600)

# ------------------------------
#  Biblioteca personal: ver, exportar, eliminar
# ------------------------------
st.markdown("---")
st.subheader("📚 Tu biblioteca personal (guardada)")

df_lib = pd.read_csv(LIBRARY_CSV, dtype=str)
if df_lib.empty:
    st.info("Aún no tienes libros guardados.")
else:
    # filtrar por nickname
    my_lib = df_lib[df_lib["nickname"] == nickname]
    st.write(f"Mostrando biblioteca de: **{nickname}** — {len(my_lib)} items")
    if not my_lib.empty:
        st.dataframe(my_lib[["title","authors","source","download_url","saved_at"]].reset_index(drop=True))
        col1, col2, col3 = st.columns(3)
        with col1:
            # exportar CSV (solo los de tu nickname)
            csv = my_lib.to_csv(index=False).encode("utf-8")
            st.download_button("Exportar mi biblioteca (CSV)", data=csv, file_name=f"biblioteca_{nickname}.csv", mime="text/csv")
        with col2:
            if st.button("Eliminar TODOS los libros de mi biblioteca"):
                df_lib = df_lib[df_lib["nickname"] != nickname]
                df_lib.to_csv(LIBRARY_CSV, index=False)
                st.success("Biblioteca limpiada.")
                st.experimental_rerun()
        with col3:
            if st.button("Eliminar entradas duplicadas (global)"):
                df_lib = pd.read_csv(LIBRARY_CSV, dtype=str)
                df_lib = df_lib.drop_duplicates(subset=["nickname","book_id"])
                df_lib.to_csv(LIBRARY_CSV, index=False)
                st.success("Duplicados eliminados.")
                st.experimental_rerun()

st.markdown("---")
st.write(
    "ℹ️ **Notas importantes:**\n"
    "- Esta app usa fuentes públicas (Gutenberg via Gutendex, Open Library). Algunas obras están en dominio público y son legales para leer y descargar.\n"
    "- No garantiza que todos los resultados sean completos o siempre descargables. Verifica la licencia en la página de origen.\n"
    "- El archivo `library.csv` se guarda en el servidor de la app; su persistencia depende de dónde despliegues la app (en Streamlit Cloud suele persistir mientras la app exista, pero no es una solución de almacenamiento a prueba de fallos).\n"
    "- Para un sistema con cuentas y almacenamiento real (por usuario) te recomiendo integrar Google Sheets, Firebase o una base de datos (p. ej. Supabase)."
      )
