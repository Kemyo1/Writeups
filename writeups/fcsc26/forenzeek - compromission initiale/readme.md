Enoncé : 
Des logs réseau issues de l'outil Zeek ont été collectés sur un réseau dans lequel un attaquant a été repéré. Seule une partie des champs des logs de Zeek sont diponibles.

Une compromission a été observée sur la machine dont l'adresse IP est 192.168.1.42. Cette compromission a été réalisée via un email malveillant contenant une charge utile assez volumineuse. Pouvez-vous retrouver l'uid de la connexion associée au téléchargement du mail ? (ex: 1ac41a8ff0fd305679)

---
J'ai travaillé entièrement sur Google Sheets pour ce challenge : 

![img](./images/1.png)

On nous indique que la victime a téléchargé une pièce jointe dans un mail.
L'IP d'origine de la ligne recherchée correspond donc à celle de la victime.

![img](./images/2.png)
Le second critère pour réduire la liste : la compromission s'est fait par le téléchargement d'un 
mail malveillant. Cela correspond au Port destinataire 993 : Imap over implicit Tls.

![img](./images/3.png)

Enfin le troisième indice dans l'énoncé est que le payload du mail est assez volumineux.
La ligne recherchée est celle qui à le plus gros bytecount, 102025.
Le flag est donc FCSC{uid} avec l'uid de la ligne en question.





