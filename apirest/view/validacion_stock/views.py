from datetime import datetime
class ValidacionStock:
    def __init__(self,conn,item,almacen,ubicacion):
        self.conn = conn
        self.item = item
        self.codigo = item['codigo']
        self.lote = item['lote']
        self.fecha = item['fecha']
        self.ubicacion = ubicacion
        self.almacen = almacen
        self.estado : bool = False
  
    def validar(self):
       
        sql = f"""
                SELECT 'mom_cant' = ISNULL(
                    SUM(
                        CASE
                            WHEN mom_tipmov = 'E' THEN mom_cant
                            WHEN mom_tipmov = 'S' THEN mom_cant * -1
                        END
                    ), 0
                ) 
                FROM movm{datetime.now().year} 
                WHERE elimini = 0 
                    AND art_codigo = ?
                    AND ALM_CODIGO = ?
                    AND UBI_COD1 = ? 

                    {
                        f"AND art_codadi='{self.lote}' " if self.lote!='' else ''
                    }
                    {
                        f"AND mom_lote='{self.fecha}' " if self.fecha!='' else ''
                    }
                """
  
        cursor = self.conn.cursor()
        params = (self.codigo,self.almacen,self.ubicacion)
        cursor.execute(sql,params)
        data = cursor.fetchone()
   
        self.conn.commit()
        self.conn.close()
        self.estado =  data[0]>float(self.item['cantidad'])
        return self.estado,data[0]
