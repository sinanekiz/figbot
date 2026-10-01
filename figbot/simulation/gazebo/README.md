# Gazebo V0 ortamı

`../worlds/figbot_v0.world.sdf`, erişim ve kaba çarpışma incelemesi için kuru/yeşil incir, taş, yaprak, dal ve huni proxy'leri içerir. Meyve deformasyonu, silikon teması ve gerçek sürtünme modellenmemiştir.

Gazebo Sim kurulu bir ROS 2 ortamında:

```bash
gz sim -v 3 simulation/worlds/figbot_v0.world.sdf
```

Robot modeli `../ros2/figbot_description` paketinden spawn edilmelidir. Bu depo çalıştırmasında Gazebo ikilisi mevcut olmadığı için dünya dosyası yalnız sözdizimi/entegrasyon girdisi olarak sağlanmıştır; sonuçlar `PHYSICAL VALIDATION REQUIRED` durumundadır.

