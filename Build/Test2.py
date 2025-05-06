# shop_id'leri geri eklemek için önce veriyi tekrar okuyalım
full_test_df = pd.read_csv("C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Cvss/shop_features2.csv")

# shop_id, gerçek ve tahmin edilen grup bilgilerini birleştirelim
comparison_df = pd.DataFrame({
    'shop_id': full_test_df['shop_id'],
    'actual_group': y_new_test,
    'predicted_group': y_pred_new_test
})

# Gruplara göre sıralayalım
comparison_df = comparison_df.sort_values(by=['actual_group', 'predicted_group']).reset_index(drop=True)

# CSV olarak kaydet (isteğe bağlı)
comparison_df.to_csv("predicted_vs_actual_collusion_groups.csv", index=False)

# Ekrana yazdıralım
print("\nTahmin Edilen vs Gerçek Collusion Grupları (Shop Bazında):")
print(comparison_df)
