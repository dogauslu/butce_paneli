#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  2 08:49:30 2026

@author: mac
"""

import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px  # Yeni eklediğimiz grafik kütüphanesi

st.set_page_config(page_title="Kişisel Bütçe Paneli", page_icon="💳", layout="wide")

VERI_DOSYASI = "butce_verileri.csv"

def verileri_yukle():
    """Uygulama açıldığında CSV dosyasını okur, dosya yoksa BOŞ bir tablo oluşturur."""
    if os.path.exists(VERI_DOSYASI):
        df = pd.read_csv(VERI_DOSYASI)
        df["Tarih"] = pd.to_datetime(df["Tarih"]).dt.date
        return df
    else:
        # İçinde hiçbir veri olmayan, sadece başlıkların (kolonların) olduğu boş bir DataFrame yaratıyoruz
        bos_df = pd.DataFrame(columns=["Tarih", "Kategori", "Tür", "Tutar", "Açıklama"])
        bos_df.to_csv(VERI_DOSYASI, index=False)
        return bos_df

if 'finans_verileri' not in st.session_state:
    st.session_state['finans_verileri'] = verileri_yukle()

st.sidebar.title("Kişisel Finans")
st.sidebar.markdown("---")
secilen_sayfa = st.sidebar.radio("Menü", ["🏠 Ana Panel", "➕ İşlem Ekle", "📊 Raporlar"])

df = st.session_state['finans_verileri']

# ==========================================
# 3. ANA PANEL GÖRÜNÜMÜ
# ==========================================
if secilen_sayfa == "🏠 Ana Panel":
    st.title("💳 Bütçe Yönetimi Kontrol Paneli")
    st.markdown("---")
    
    toplam_gelir = df[df["Tür"] == "Gelir"]["Tutar"].sum()
    toplam_gider = df[df["Tür"] == "Gider"]["Tutar"].sum()
    net_bakiye = toplam_gelir - toplam_gider

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="🟢 Toplam Gelir", value=f"{toplam_gelir:,.2f} TL")
    with col2:
        st.metric(label="🔴 Toplam Gider", value=f"{toplam_gider:,.2f} TL")
    with col3:
        st.metric(label="💰 Kalan Bakiye", value=f"{net_bakiye:,.2f} TL", delta=f"{net_bakiye:,.2f} TL")

    st.markdown("---")
    st.subheader("📋 Geçmiş İşlemler")
    st.dataframe(df.sort_values(by="Tarih", ascending=False), use_container_width=True, hide_index=True)

# ==========================================
# 4. İŞLEM EKLEME GÖRÜNÜMÜ
# ==========================================
elif secilen_sayfa == "➕ İşlem Ekle":
    st.title("➕ Yeni İşlem Ekle")
    st.markdown("Aşağıdaki formu doldurarak sisteme yeni bir kayıt girebilirsiniz.")
    
    with st.form("islem_formu", clear_on_submit=True):
        col_form1, col_form2 = st.columns(2)
        
        with col_form1:
            islem_tarihi = st.date_input("Tarih", datetime.date.today())
            islem_turu = st.selectbox("İşlem Türü", ["Gider", "Gelir"])
        
        with col_form2:
            kategoriler = ["Maaş", "Yatırım", "Burs"] if islem_turu == "Gelir" else ["Market", "Fatura", "Eğlence", "Eğitim", "Sağlık", "Diğer"]
            kategori = st.selectbox("Kategori", kategoriler)
            tutar = st.number_input("Tutar (TL)", min_value=0.0, step=10.0, format="%.2f")
        
        aciklama = st.text_input("Açıklama (Opsiyonel)")
        
        kaydet_butonu = st.form_submit_button("💾 İşlemi Kaydet")
        
        if kaydet_butonu:
            if tutar > 0:
                yeni_kayit = pd.DataFrame({
                    "Tarih": [islem_tarihi],
                    "Kategori": [kategori],
                    "Tür": [islem_turu],
                    "Tutar": [tutar],
                    "Açıklama": [aciklama]
                })
                
                st.session_state['finans_verileri'] = pd.concat([st.session_state['finans_verileri'], yeni_kayit], ignore_index=True)
                st.session_state['finans_verileri'].to_csv(VERI_DOSYASI, index=False)
                
                st.success("İşlem başarıyla eklendi ve kalıcı olarak kaydedildi!")
            else:
                st.error("Lütfen 0'dan büyük geçerli bir tutar giriniz!")

# ==========================================
# 5. RAPORLAR GÖRÜNÜMÜ (YENİ EKLENEN KISIM)
# ==========================================
elif secilen_sayfa == "📊 Raporlar":
    st.title("📊 Finansal Analiz ve Raporlar")
    st.markdown("---")
    
    # Sadece giderleri filtreliyoruz
    giderler_df = df[df["Tür"] == "Gider"]
    
    if not giderler_df.empty:
        col_grafik1, col_grafik2 = st.columns(2)
        
        with col_grafik1:
            st.subheader("Kategori Bazlı Harcamalar")
            # Kategorilere göre toplam harcamayı hesaplayıp Halka (Donut) grafik çiziyoruz
            kategori_toplam = giderler_df.groupby("Kategori")["Tutar"].sum().reset_index()
            fig_pie = px.pie(kategori_toplam, values='Tutar', names='Kategori', hole=0.4, 
                             color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_grafik2:
            st.subheader("Günlük Harcama Trendi")
            # Tarihe göre harcamaları topluyoruz
            gunluk_toplam = giderler_df.groupby("Tarih")["Tutar"].sum().reset_index()
            
            # Grafiği oluştururken 'text_auto' ekleyip sütunların üstüne değerleri yazdırıyoruz
            fig_bar = px.bar(gunluk_toplam, x='Tarih', y='Tutar', 
                             color='Tutar', color_continuous_scale='Reds',
                             text_auto='.0f') # .0f değerleri küsuratsız tam sayı yazar
            
            # --- LABEL (ETİKET) DÜZELTMELERİ ---
            fig_bar.update_layout(
                xaxis_tickangle=-45,   # X eksenindeki tarih yazılarını 45 derece eğer
                margin=dict(b=80),     # Alt kısma (bottom) yazılar sığsın diye ekstra boşluk bırakır
                xaxis_title="",        # 'Tarih' eksen başlığını gizleyerek grafiğe yer açar
                yaxis_title=""         # 'Tutar' eksen başlığını gizler
            )
            
            # Tarihleri kesintisiz bir zaman çizelgesi yerine yan yana dizilmiş kutular (kategori) gibi gösterir
            fig_bar.update_xaxes(type='category')
            
            # Sütun üzerindeki sayısal değerleri sütunun hemen üstüne (dışına) taşır
            fig_bar.update_traces(textposition='outside') 
            
            st.plotly_chart(fig_bar, use_container_width=True) 
    else:
        st.info("📊 Grafik oluşturabilmek için henüz hiç gider kaydınız bulunmuyor. İşlem Ekle sayfasından gider ekleyebilirsiniz.")