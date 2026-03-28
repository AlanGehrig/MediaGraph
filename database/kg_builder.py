"""
Neo4j 知识图谱构建模块
管理人物、媒体、时间、地点等节点的增删改查
"""
import os
import uuid
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional

from loguru import logger

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class KGBuilder:
    """
    Neo4j 知识图谱构建器
    提供人物-媒体-时间-地点的关联存储和查询
    """
    
    def __init__(self, uri: str, user: str, password: str):
        """
        初始化Neo4j连接
        
        Args:
            uri: Neo4j连接URI (bolt://localhost:7687)
            user: 用户名
            password: 密码
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        
        self._connect()
    
    def _connect(self):
        """建立Neo4j连接"""
        try:
            from neo4j import GraphDatabase
            
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            
            # 验证连接
            with self.driver.session() as session:
                result = session.run("RETURN 1")
                result.single()
            
            logger.info(f"✅ Neo4j连接成功: {self.uri}")
            
        except ImportError:
            logger.warning("neo4j驱动未安装，使用模拟模式")
            self.driver = None
        except Exception as e:
            logger.warning(f"Neo4j连接失败: {e}，使用模拟模式")
            self.driver = None
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            self.driver = None
    
    def _get_session(self):
        """获取数据库会话"""
        if self.driver is None:
            raise RuntimeError("Neo4j未连接")
        return self.driver.session()
    
    # ========== 节点创建 ==========
    
    def add_person(self, name: str, metadata: Dict = None) -> str:
        """
        添加人物节点
        
        Args:
            name: 人物名称
            metadata: 附加信息
            
        Returns:
            person_node_id
        """
        person_id = str(uuid.uuid4())[:12]
        metadata = metadata or {}
        
        if self.driver is None:
            return person_id
        
        try:
            with self._get_session() as session:
                session.run("""
                    MERGE (p:Person {name: $name})
                    SET p.person_id = $person_id,
                        p.created_at = datetime(),
                        p.metadata = $metadata
                """, name=name, person_id=person_id, metadata=metadata)
            
            return person_id
            
        except Exception as e:
            logger.error(f"添加人物失败: {e}")
            return person_id
    
    def add_media(
        self,
        path: str,
        metadata: Dict = None,
        media_id: Optional[str] = None
    ) -> str:
        """
        添加媒体节点
        
        Args:
            path: 文件路径
            metadata: 媒体元数据(场景、情绪、光线等)
            media_id: 指定媒体ID
            
        Returns:
            media_node_id
        """
        if media_id is None:
            media_id = hashlib.md5(path.encode()).hexdigest()[:12]
        
        metadata = metadata or {}
        
        if self.driver is None:
            return media_id
        
        try:
            with self._get_session() as session:
                session.run("""
                    MERGE (m:Media {media_id: $media_id})
                    SET m.path = $path,
                        m.filename = $filename,
                        m.created_at = datetime(),
                        m.scene = $scene,
                        m.mood = $mood,
                        m.lighting = $lighting,
                        m.tags = $tags,
                        m.metadata = $metadata
                """,
                    media_id=media_id,
                    path=path,
                    filename=os.path.basename(path),
                    scene=metadata.get('scene', ''),
                    mood=metadata.get('mood', ''),
                    lighting=metadata.get('lighting', ''),
                    tags=metadata.get('tags', ''),
                    metadata=metadata
                )
            
            return media_id
            
        except Exception as e:
            logger.error(f"添加媒体失败: {e}")
            return media_id
    
    def add_location(self, location: str, metadata: Dict = None) -> str:
        """
        添加地点节点
        
        Args:
            location: 地点名称
            metadata: 附加信息
            
        Returns:
            location_node_id
        """
        location_id = hashlib.md5(location.encode()).hexdigest()[:12]
        metadata = metadata or {}
        
        if self.driver is None:
            return location_id
        
        try:
            with self._get_session() as session:
                session.run("""
                    MERGE (l:Location {location_id: $location_id})
                    SET l.name = $name,
                        l.created_at = datetime(),
                        l.metadata = $metadata
                """, location_id=location_id, name=location, metadata=metadata)
            
            return location_id
            
        except Exception as e:
            logger.error(f"添加地点失败: {e}")
            return location_id
    
    def add_time(self, timestamp: str, date: str = None, metadata: Dict = None) -> str:
        """
        添加时间节点
        
        Args:
            timestamp: ISO格式时间戳
            date: 简化的日期 YYYY-MM-DD
            
        Returns:
            time_node_id
        """
        time_id = hashlib.md5(timestamp.encode()).hexdigest()[:12]
        metadata = metadata or {}
        
        if self.driver is None:
            return time_id
        
        try:
            with self._get_session() as session:
                session.run("""
                    MERGE (t:Time {time_id: $time_id})
                    SET t.timestamp = $timestamp,
                        t.date = $date,
                        t.year = $year,
                        t.month = $month,
                        t.day = $day,
                        t.metadata = $metadata
                """,
                    time_id=time_id,
                    timestamp=timestamp,
                    date=date or timestamp[:10],
                    year=int(timestamp[:4]) if timestamp else None,
                    month=int(timestamp[5:7]) if len(timestamp) > 5 else None,
                    day=int(timestamp[8:10]) if len(timestamp) > 8 else None,
                    metadata=metadata
                )
            
            return time_id
            
        except Exception as e:
            logger.error(f"添加时间失败: {e}")
            return time_id
    
    # ========== 关系创建 ==========
    
    def relate_person_media(
        self,
        person_id: str,
        media_id: str,
        relation: str = "APPEARS_IN"
    ):
        """
        建立人物-媒体关系
        
        Args:
            person_id: 人物ID
            media_id: 媒体ID
            relation: 关系类型 (APPEARS_IN, CAPTURED_BY, etc.)
        """
        if self.driver is None:
            return
        
        try:
            with self._get_session() as session:
                session.run("""
                    MATCH (p:Person {person_id: $person_id})
                    MATCH (m:Media {media_id: $media_id})
                    MERGE (p)-[r:APPEARS_IN]->(m)
                    SET r.created_at = datetime(),
                        r.relation = $relation
                """, person_id=person_id, media_id=media_id, relation=relation)
                
        except Exception as e:
            logger.error(f"建立人物-媒体关系失败: {e}")
    
    def relate_media_location(
        self,
        media_id: str,
        location_id: str
    ):
        """建立媒体-地点关系"""
        if self.driver is None:
            return
        
        try:
            with self._get_session() as session:
                session.run("""
                    MATCH (m:Media {media_id: $media_id})
                    MATCH (l:Location {location_id: $location_id})
                    MERGE (m)-[r:LOCATED_AT]->(l)
                    SET r.created_at = datetime()
                """, media_id=media_id, location_id=location_id)
                
        except Exception as e:
            logger.error(f"建立媒体-地点关系失败: {e}")
    
    def relate_media_time(
        self,
        media_id: str,
        time_id: str
    ):
        """建立媒体-时间关系"""
        if self.driver is None:
            return
        
        try:
            with self._get_session() as session:
                session.run("""
                    MATCH (m:Media {media_id: $media_id})
                    MATCH (t:Time {time_id: $time_id})
                    MERGE (m)-[r:CAPTURED_AT]->(t)
                    SET r.created_at = datetime()
                """, media_id=media_id, time_id=time_id)
                
        except Exception as e:
            logger.error(f"建立媒体-时间关系失败: {e}")
    
    # ========== 查询方法 ==========
    
    def get_all_persons(self, min_media_count: int = 1) -> List[Dict]:
        """获取所有人物节点"""
        if self.driver is None:
            return []
        
        try:
            with self._get_session() as session:
                result = session.run("""
                    MATCH (p:Person)-[r:APPEARS_IN]->(m:Media)
                    WITH p, count(m) as media_count
                    WHERE media_count >= $min_count
                    RETURN p.person_id as id,
                           p.name as name,
                           media_count,
                           p.metadata as metadata
                    ORDER BY media_count DESC
                """, min_count=min_media_count)
                
                return [dict(record) for record in result]
                
        except Exception as e:
            logger.error(f"获取人物列表失败: {e}")
            return []
    
    def get_person_detail(self, person_id: str) -> Optional[Dict]:
        """获取人物详情"""
        if self.driver is None:
            return None
        
        try:
            with self._get_session() as session:
                result = session.run("""
                    MATCH (p:Person {person_id: $person_id})
                    OPTIONAL MATCH (p)-[r:APPEARS_IN]->(m:Media)
                    WITH p, count(m) as media_count, collect(m) as media_list
                    RETURN p.person_id as id,
                           p.name as name,
                           media_count,
                           p.metadata as metadata,
                           [(m) | {media_id: m.media_id, path: m.path}] as media
                """, person_id=person_id)
                
                record = result.single()
                return dict(record) if record else None
                
        except Exception as e:
            logger.error(f"获取人物详情失败: {e}")
            return None
    
    def get_person_media(self, person_id: str, limit: int = 50) -> List[Dict]:
        """获取人物关联的媒体"""
        if self.driver is None:
            return []
        
        try:
            with self._get_session() as session:
                result = session.run("""
                    MATCH (p:Person {person_id: $person_id})-[r:APPEARS_IN]->(m:Media)
                    RETURN m.media_id as media_id,
                           m.path as path,
                           m.filename as filename,
                           m.scene as scene,
                           m.mood as mood
                    ORDER BY m.created_at DESC
                    LIMIT $limit
                """, person_id=person_id, limit=limit)
                
                return [dict(record) for record in result]
                
        except Exception as e:
            logger.error(f"获取人物媒体失败: {e}")
            return []
    
    def get_timeline(
        self,
        start_date: str = None,
        end_date: str = None,
        granularity: str = "day"
    ) -> List[Dict]:
        """获取时间线"""
        if self.driver is None:
            return []
        
        try:
            with self._get_session() as session:
                if granularity == "day":
                    query = """
                        MATCH (m:Media)-[:CAPTURED_AT]->(t:Time)
                        WHERE t.date IS NOT NULL
                        AND ($start_date IS NULL OR t.date >= $start_date)
                        AND ($end_date IS NULL OR t.date <= $end_date)
                        RETURN t.date as date,
                               count(m) as count,
                               collect(m.media_id) as media_ids
                        ORDER BY date
                    """
                elif granularity == "month":
                    query = """
                        MATCH (m:Media)-[:CAPTURED_AT]->(t:Time)
                        WHERE t.year IS NOT NULL AND t.month IS NOT NULL
                        AND ($start_date IS NULL OR t.date >= $start_date)
                        AND ($end_date IS NULL OR t.date <= $end_date)
                        RETURN t.year + '-' + CASE WHEN t.month < 10 THEN '0' ELSE '' END + t.month as date,
                               count(m) as count,
                               collect(m.media_id) as media_ids
                        ORDER BY date
                    """
                else:
                    query = """
                        MATCH (m:Media)-[:CAPTURED_AT]->(t:Time)
                        WHERE t.year IS NOT NULL
                        RETURN toString(t.year) as date,
                               count(m) as count,
                               collect(m.media_id) as media_ids
                        ORDER BY date
                    """
                
                result = session.run(query, start_date=start_date, end_date=end_date)
                return [dict(record) for record in result]
                
        except Exception as e:
            logger.error(f"获取时间线失败: {e}")
            return []
    
    def get_all_locations(self, min_count: int = 1) -> List[Dict]:
        """获取所有地点"""
        if self.driver is None:
            return []
        
        try:
            with self._get_session() as session:
                result = session.run("""
                    MATCH (m:Media)-[r:LOCATED_AT]->(l:Location)
                    WITH l, count(m) as media_count
                    WHERE media_count >= $min_count
                    RETURN l.location_id as id,
                           l.name as name,
                           media_count,
                           l.metadata as metadata
                    ORDER BY media_count DESC
                """, min_count=min_count)
                
                return [dict(record) for record in result]
                
        except Exception as e:
            logger.error(f"获取地点列表失败: {e}")
            return []
    
    def get_location_media(self, location_id: str, limit: int = 50) -> List[Dict]:
        """获取地点关联的媒体"""
        if self.driver is None:
            return []
        
        try:
            with self._get_session() as session:
                result = session.run("""
                    MATCH (m:Media)-[:LOCATED_AT]->(l:Location {location_id: $location_id})
                    RETURN m.media_id as media_id,
                           m.path as path,
                           m.filename as filename
                    ORDER BY m.created_at DESC
                    LIMIT $limit
                """, location_id=location_id, limit=limit)
                
                return [dict(record) for record in result]
                
        except Exception as e:
            logger.error(f"获取地点媒体失败: {e}")
            return []
    
    def get_relations(
        self,
        center_id: str,
        center_type: str = "media",
        max_depth: int = 2
    ) -> Dict:
        """获取关系网络"""
        if self.driver is None:
            return {"nodes": [], "edges": []}
        
        try:
            with self._get_session() as session:
                if center_type == "media":
                    query = """
                        MATCH path=(m:Media {media_id: $center_id})-[*1..%d]-(other)
                        WITH nodes(path) as ns, rels(path) as rs
                        UNWIND ns as n
                        WITH collect(DISTINCT n) as nodes, rs
                        UNWIND rs as r
                        WITH nodes, collect(DISTINCT r) as edges
                        RETURN nodes, edges
                    """ % max_depth
                else:
                    query = """
                        MATCH path=(p:Person {person_id: $center_id})-[*1..%d]-(other)
                        WITH nodes(path) as ns, rels(path) as rs
                        UNWIND ns as n
                        WITH collect(DISTINCT n) as nodes, rs
                        UNWIND rs as r
                        WITH nodes, collect(DISTINCT r) as edges
                        RETURN nodes, edges
                    """ % max_depth
                
                result = session.run(query, center_id=center_id)
                record = result.single()
                
                if record:
                    nodes = []
                    edges = []
                    
                    for node in record['nodes']:
                        node_type = list(node.labels)[0]
                        nodes.append({
                            'id': node.get('media_id') or node.get('person_id') or node.get('location_id'),
                            'type': node_type,
                            'name': node.get('name') or node.get('filename', ''),
                        })
                    
                    for rel in record['edges']:
                        edges.append({
                            'source': rel.start_node.get('media_id') or rel.start_node.get('person_id'),
                            'target': rel.end_node.get('media_id') or rel.end_node.get('person_id'),
                            'type': type(rel).__name__,
                        })
                    
                    return {"nodes": nodes, "edges": edges}
                
                return {"nodes": [], "edges": []}
                
        except Exception as e:
            logger.error(f"获取关系网络失败: {e}")
            return {"nodes": [], "edges": []}
    
    def get_graph_stats(self) -> Dict:
        """获取图谱统计"""
        if self.driver is None:
            return {
                'total_media': 0,
                'total_persons': 0,
                'total_locations': 0,
                'total_faces': 0,
                'total_tags': 0,
            }
        
        try:
            with self._get_session() as session:
                result = session.run("""
                    MATCH (m:Media) WHERE m:Media
                    OPTIONAL MATCH (p:Person) WHERE p:Person
                    OPTIONAL MATCH (l:Location) WHERE l:Location
                    RETURN count(DISTINCT m) as total_media,
                           count(DISTINCT p) as total_persons,
                           count(DISTINCT l) as total_locations
                """)
                
                record = result.single()
                
                stats = dict(record) if record else {}
                stats['total_tags'] = 0  # 需要额外查询
                
                return stats
                
        except Exception as e:
            logger.error(f"获取图谱统计失败: {e}")
            return {}
    
    def query_by_nl(self, nl_query: Dict) -> List[Dict]:
        """
        自然语言查询
        
        将解析后的自然语言查询转换为Cypher执行
        
        Args:
            nl_query: parse_nl_query返回的结构化查询
            
        Returns:
            匹配的媒体列表
        """
        if self.driver is None:
            return []
        
        try:
            with self._get_session() as session:
                # 构建查询条件
                conditions = []
                params = {}
                
                # 场景过滤
                if nl_query.get('scene'):
                    scene_conditions = " OR ".join([f"m.scene CONTAINS '${s}'" for s in nl_query['scene']])
                    conditions.append(f"({scene_conditions})")
                
                # 情绪过滤
                if nl_query.get('mood'):
                    mood_conditions = " OR ".join([f"m.mood CONTAINS '${m}'" for m in nl_query['mood']])
                    conditions.append(f"({mood_conditions})")
                
                # 光线过滤
                if nl_query.get('lighting'):
                    light_conditions = " OR ".join([f"m.lighting CONTAINS '${l}'" for l in nl_query['lighting']])
                    conditions.append(f"({light_conditions})")
                
                # 人物过滤
                if nl_query.get('person'):
                    person_name = nl_query['person']
                    query = f"""
                        MATCH (p:Person)-[:APPEARS_IN]->(m:Media)
                        WHERE p.name CONTAINS '${person_name}'
                        RETURN DISTINCT m.media_id as media_id,
                               m.path as path,
                               m.filename as filename,
                               0.8 as similarity,
                               m.scene as snippet
                        LIMIT 50
                    """
                    result = session.run(query)
                    return [dict(record) for record in result]
                
                # 地点过滤
                if nl_query.get('location'):
                    location_name = nl_query['location']
                    query = f"""
                        MATCH (m:Media)-[:LOCATED_AT]->(l:Location)
                        WHERE l.name CONTAINS '${location_name}'
                        RETURN DISTINCT m.media_id as media_id,
                               m.path as path,
                               m.filename as filename,
                               0.8 as similarity,
                               m.scene as snippet
                        LIMIT 50
                    """
                    result = session.run(query)
                    return [dict(record) for record in result]
                
                # 通用属性查询
                if conditions:
                    where_clause = " AND ".join(conditions)
                    query = f"""
                        MATCH (m:Media)
                        WHERE {where_clause}
                        RETURN m.media_id as media_id,
                               m.path as path,
                               m.filename as filename,
                               0.7 as similarity,
                               m.scene as snippet
                        LIMIT 50
                    """
                    result = session.run(query)
                    return [dict(record) for record in result]
                
                return []
                
        except Exception as e:
            logger.error(f"自然语言查询失败: {e}")
            return []
    
    def get_scene_distribution(self) -> List[Dict]:
        """获取场景分布"""
        if self.driver is None:
            return []
        
        try:
            with self._get_session() as session:
                result = session.run("""
                    MATCH (m:Media)
                    WHERE m.scene IS NOT NULL
                    RETURN m.scene as scene,
                           count(*) as count
                    ORDER BY count DESC
                """)
                
                return [dict(record) for record in result]
                
        except Exception as e:
            logger.error(f"获取场景分布失败: {e}")
            return []
    
    def get_mood_distribution(self) -> List[Dict]:
        """获取情绪分布"""
        if self.driver is None:
            return []
        
        try:
            with self._get_session() as session:
                result = session.run("""
                    MATCH (m:Media)
                    WHERE m.mood IS NOT NULL
                    RETURN m.mood as mood,
                           count(*) as count
                    ORDER BY count DESC
                """)
                
                return [dict(record) for record in result]
                
        except Exception as e:
            logger.error(f"获取情绪分布失败: {e}")
            return []
    
    def get_tag_stats(self, limit: int = 50) -> List[Dict]:
        """获取标签统计"""
        if self.driver is None:
            return []
        
        try:
            with self._get_session() as session:
                result = session.run("""
                    MATCH (m:Media)
                    WHERE m.tags IS NOT NULL
                    WITH m, split(m.tags, ',') as tagList
                    UNWIND tagList as tag
                    RETURN tag as tag_name,
                           count(*) as count
                    ORDER BY count DESC
                    LIMIT $limit
                """, limit=limit)
                
                return [dict(record) for record in result]
                
        except Exception as e:
            logger.error(f"获取标签统计失败: {e}")
            return []
