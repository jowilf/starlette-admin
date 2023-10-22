# Yayınlama

**Starlette-Admin** ile FastAPI veya Starlette kullanıp kullanmamanız fark etmeksizin, yayınlama sürecinde size yol gösterecek çok iyi kaynaklar hali hazırda mevcut.
Detaylı bilgi ve en iyi pratikleri sunan bu kaynaklara başvurmanız şiddetle tavsiye edilir:

* [FastAPI Deployment Documentation](https://fastapi.tiangolo.com/deployment/)
* [Uvicorn Deployment Documentation](https://www.uvicorn.org/deployment)

Ancak, Traefik veya Nginx gibi bir proxy sunucunun arkasında uygulamanızı çalıştırırken, statik dosyaların HTTPS bağlantıları olarak derlenmemesi gibi bir sorunla karşılaşabilirsiniz. Bu sorunu çözmek için aşağıdaki adımları izleyin:

1. Proxy sunucunuzun HTTPS trafiğini yönetebilecek şekilde konfigüre edildiğinden emin olun.
2. Uygulamanızı Uvicorn ile başlatırken, `--forwarded-allow-ips` ve `--proxy-headers` opsiyonlarını kullanın. Bu opsiyonlar, Uvicorn'un proxy sunucudan gelen yönlendirilmiş headerları doğru bir şekilde işlemesini sağlar.

```shell title="Example"
uvicorn app.main:app --forwarded-allow-ips='*' --proxy-headers
```
