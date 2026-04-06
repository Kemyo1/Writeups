Enoncé : 
Des logs réseau issues de l'outil Zeek ont été collectés sur un réseau dans lequel un attaquant a été repéré. Seule une partie des champs des logs de Zeek sont diponibles.

Une compromission a été observée sur la machine dont l'adresse IP est 192.168.1.42. Cette compromission a été réalisée via un email malveillant contenant une charge utile assez volumineuse. Pouvez-vous retrouver l'uid de la connexion associée au téléchargement du mail ? (ex: 1ac41a8ff0fd305679)

---
J'ai travaillé entièrement sur Google Sheets pour ce challenge : 

On nous indique que la victime a téléchargé une pièce jointe dans un mail.
L'IP d'origine de la ligne recherchée correspond donc à celle de la victime.

Le second critère pour réduire la liste : la compromission s'est fait par le téléchargement d'un 
mail malveillant. Cela correspond au Port destinataire 993 : Imap over implicit Tls.

Enfin le troisième indice dans l'énoncé est que le payload du mail est assez volumineux.
La ligne recherchée est celle qui à le plus gros bytecount, et le flag est donc FCSC{uid} avec l'uid de cette ligne.





